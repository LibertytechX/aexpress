// API Service for Dispatcher Frontend
const API_BASE_URL = 'http://localhost:8000/api';

// Get stored auth token
const getToken = () => localStorage.getItem('access_token');

// Helper for authenticated requests
const authHeaders = () => {
    const token = getToken();
    return {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
};

// ─── AUTHENTICATION ─────────────────────────────────────────────
export const AuthAPI = {
    async login(phone, password) {
        const res = await fetch(`${API_BASE_URL}/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, password })
        });
        const data = await res.json();
        if (!res.ok) throw data;
        // Backend returns tokens nested: { tokens: { access, refresh } }
        const tokens = data.tokens || data;
        if (tokens.access) localStorage.setItem('access_token', tokens.access);
        if (tokens.refresh) localStorage.setItem('refresh_token', tokens.refresh);
        return data;
    },

    logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    },

    isAuthenticated() {
        return !!getToken();
    }
};

// ─── RIDERS ─────────────────────────────────────────────────────
export const RidersAPI = {
    async getAll() {
        const res = await fetch(`${API_BASE_URL}/dispatch/riders/`, {
            headers: authHeaders()
        });
        if (!res.ok) throw new Error('Failed to fetch riders');
        const data = await res.json();
        // Transform backend data to match frontend interface
        return data.map(r => ({
            id: r.rider_id || r.id,
            name: r.name || 'Unknown',
            phone: r.phone || '',
            vehicle: r.vehicle || 'Bike',
            status: r.status || 'offline',
            currentOrder: r.current_order || null,
            todayOrders: r.todayOrders || 0,
            todayEarnings: r.todayEarnings || 0,
            rating: parseFloat(r.rating) || 4.5,
            totalDeliveries: r.total_deliveries || 0,
            completionRate: r.completionRate || 95,
            avgTime: r.avgTime || '30 min',
            joined: r.joined || 'N/A',
            lat: r.current_latitude ? parseFloat(r.current_latitude) : null,
            lng: r.current_longitude ? parseFloat(r.current_longitude) : null,
            lastLocationUpdate: r.last_location_update || null,
            _uuid: r.id  // keep raw UUID for update_location calls
        }));
    },

    async updateLocation(riderUuid, lat, lng) {
        const res = await fetch(`${API_BASE_URL}/dispatch/riders/${riderUuid}/update_location/`, {
            method: 'PATCH',
            headers: authHeaders(),
            body: JSON.stringify({ lat, lng })
        });
        if (!res.ok) throw new Error('Failed to update rider location');
        return await res.json();
    },

    async createRider(fields) {
        // Build multipart/form-data (endpoint uses MultiPartParser)
        const form = new FormData();
        Object.entries(fields).forEach(([k, v]) => {
            if (v !== null && v !== undefined && v !== '') form.append(k, v);
        });
        const token = localStorage.getItem('access_token');
        const res = await fetch(`${API_BASE_URL}/dispatch/riders/onboarding/`, {
            method: 'POST',
            headers: token ? { 'Authorization': `Bearer ${token}` } : {},
            body: form
        });
        const data = await res.json();
        if (!res.ok) throw data;
        return data;
    }
};

// ─── ORDERS ─────────────────────────────────────────────────────
// Normalize a single order object from backend (snake_case) to frontend (camelCase)
const normalizeOrder = (o) => ({
    id: o.id || 'N/A',
    customer: o.customer || 'Unknown',
    customerPhone: o.customerPhone || '',
    merchant: o.merchant || 'Unknown',
    pickup: o.pickup || '',
    dropoff: o.dropoff || '',
    rider: o.rider || null,
    riderId: o.riderId || null,
    status: o.status || 'Pending',
    amount: parseFloat(o.amount) || 0,
    cod: parseFloat(o.cod) || 0,
    codFee: parseFloat(o.codFee) || 0,
    vehicle: o.vehicle || 'Bike',
    created: o.created || new Date().toLocaleString(),
    pkg: o.pkg || 'Box',
    // Relay routing fields
    isRelayOrder: o.is_relay_order || false,
    routingStatus: o.routing_status || 'ready',
    routingError: o.routing_error || '',
    relayLegsCount: o.relay_legs_count || 0,
    suggestedRiderId: o.suggested_rider_id || null,
    pickupLat: o.pickup_lat || null,
    pickupLng: o.pickup_lng || null,
    dropoffLat: o.dropoff_lat || null,
    dropoffLng: o.dropoff_lng || null,
    relayLegs: o.relay_legs || [],
});

export const OrdersAPI = {
    async getAll() {
        const res = await fetch(`${API_BASE_URL}/dispatch/orders/`, {
            headers: authHeaders()
        });
        if (!res.ok) throw new Error('Failed to fetch orders');
        const data = await res.json();
        return data.map(normalizeOrder);
    },

    async getOne(orderNumber) {
        const res = await fetch(`${API_BASE_URL}/dispatch/orders/${orderNumber}/`, {
            headers: authHeaders()
        });
        if (!res.ok) throw new Error('Failed to fetch order');
        const data = await res.json();
        return normalizeOrder(data);
    },

    async create(orderData) {
        const res = await fetch(`${API_BASE_URL}/dispatch/orders/`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(orderData)
        });
        let data;
        try {
            data = await res.json();
        } catch (e) {
            throw new Error('Failed to create order');
        }
        if (!res.ok) {
            throw data || new Error('Failed to create order');
        }
        return normalizeOrder(data);
    },

    async assignRider(orderNumber, riderId) {
        const res = await fetch(`${API_BASE_URL}/dispatch/orders/${orderNumber}/assign_rider/`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ rider_id: riderId })
        });
        if (!res.ok) throw new Error('Failed to assign rider');
        return await res.json();
    },

    async updateStatus(orderNumber, newStatus) {
        const res = await fetch(`${API_BASE_URL}/dispatch/orders/${orderNumber}/update_status/`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ status: newStatus })
        });
        if (!res.ok) throw new Error('Failed to update status');
        return await res.json();
    },

    async generateRelayRoute(orderNumber, force = false) {
        const res = await fetch(`${API_BASE_URL}/dispatch/orders/${orderNumber}/generate-relay-route/`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ force })
        });
        let data;
        try { data = await res.json(); } catch (e) { throw new Error('Failed to generate relay route'); }
        if (!res.ok) throw data || new Error('Failed to generate relay route');
        return normalizeOrder(data);
    }
};

// ─── MERCHANTS ──────────────────────────────────────────────────
export const MerchantsAPI = {
    async getAll() {
        const res = await fetch(`${API_BASE_URL}/dispatch/merchants/`, {
            headers: authHeaders()
        });
        if (!res.ok) throw new Error('Failed to fetch merchants');
        const data = await res.json();
        return data.map(m => ({
            id: m.id || 'N/A',
            name: m.name || 'Unknown',
            contact: m.contact || '',
            phone: m.phone || '',
            category: m.category || 'General',
            totalOrders: m.totalOrders || 0,
            monthOrders: m.monthOrders || 0,
            walletBalance: parseFloat(m.walletBalance) || 0,
            status: m.status || 'Active',
            joined: m.joined || 'N/A'
        }));
    }
};

// ─── VEHICLES ───────────────────────────────────────────────────
export const VehiclesAPI = {
    async getAll() {
        const res = await fetch(`${API_BASE_URL}/orders/vehicles/`, {
            headers: authHeaders()
        });
        if (!res.ok) throw new Error('Failed to fetch vehicles');
        const data = await res.json();
        // Response shape is { success: true, vehicles: [...] }
        return Array.isArray(data) ? data : (data.vehicles || []);
    },

    async update(id, data) {
        const res = await fetch(`${API_BASE_URL}/orders/vehicles/${id}/`, {
            method: 'PATCH',
            headers: authHeaders(),
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('Failed to update vehicle');
        return await res.json();
    }
};

// ─── ACTIVITY FEED ──────────────────────────────────────────────
export const ActivityFeedAPI = {
    async getRecent(limit = 50) {
        const res = await fetch(`${API_BASE_URL}/dispatch/activity/?limit=${limit}`, {
            headers: authHeaders()
        });
        if (!res.ok) throw new Error('Failed to fetch activity feed');
        return await res.json();
    },

    async getAblyToken() {
        const res = await fetch(`${API_BASE_URL}/dispatch/ably-token/`, {
            headers: authHeaders()
        });
        if (!res.ok) throw new Error('Failed to get Ably token');
        return await res.json();
    }
};

// ─── SETTINGS ───────────────────────────────────────────────────
export const SettingsAPI = {
    async get() {
        const res = await fetch(`${API_BASE_URL}/dispatch/settings/`, {
            headers: authHeaders()
        });
        if (!res.ok) throw new Error('Failed to fetch settings');
        return await res.json();
    },

    async update(settings) {
        const res = await fetch(`${API_BASE_URL}/dispatch/settings/`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(settings)
        });
        if (!res.ok) throw new Error('Failed to update settings');
        return await res.json();
    }
};

// ─── ZONES ──────────────────────────────────────────────────────
export const ZonesAPI = {
    async getAll() {
        const res = await fetch(`${API_BASE_URL}/dispatch/zones/`, {
            headers: authHeaders()
        });
        if (!res.ok) throw new Error('Failed to fetch zones');
        const data = await res.json();
        return Array.isArray(data) ? data : (data.results || []);
    },

    async create(zone) {
        const res = await fetch(`${API_BASE_URL}/dispatch/zones/`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(zone)
        });
        if (!res.ok) throw new Error('Failed to create zone');
        return await res.json();
    },

    async update(id, zone) {
        const res = await fetch(`${API_BASE_URL}/dispatch/zones/${id}/`, {
            method: 'PATCH',
            headers: authHeaders(),
            body: JSON.stringify(zone)
        });
        if (!res.ok) throw new Error('Failed to update zone');
        return await res.json();
    },

    async remove(id) {
        const res = await fetch(`${API_BASE_URL}/dispatch/zones/${id}/`, {
            method: 'DELETE',
            headers: authHeaders()
        });
        if (!res.ok) throw new Error('Failed to delete zone');
    }
};

// ─── RELAY NODES ─────────────────────────────────────────────────
export const RelayNodesAPI = {
    async getAll() {
        const res = await fetch(`${API_BASE_URL}/dispatch/relay-nodes/`, {
            headers: authHeaders()
        });
        if (!res.ok) throw new Error('Failed to fetch relay nodes');
        const data = await res.json();
        return Array.isArray(data) ? data : (data.results || []);
    },

    async create(node) {
        const res = await fetch(`${API_BASE_URL}/dispatch/relay-nodes/`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(node)
        });
        if (!res.ok) throw new Error('Failed to create relay node');
        return await res.json();
    },

    async update(id, node) {
        const res = await fetch(`${API_BASE_URL}/dispatch/relay-nodes/${id}/`, {
            method: 'PATCH',
            headers: authHeaders(),
            body: JSON.stringify(node)
        });
        if (!res.ok) throw new Error('Failed to update relay node');
        return await res.json();
    },

    async remove(id) {
        const res = await fetch(`${API_BASE_URL}/dispatch/relay-nodes/${id}/`, {
            method: 'DELETE',
            headers: authHeaders()
        });
        if (!res.ok) throw new Error('Failed to delete relay node');
    }
};

