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
    }
};

// ─── ORDERS ─────────────────────────────────────────────────────
export const OrdersAPI = {
    async getAll() {
        const res = await fetch(`${API_BASE_URL}/dispatch/orders/`, {
            headers: authHeaders()
        });
        if (!res.ok) throw new Error('Failed to fetch orders');
        const data = await res.json();
        // Transform backend data to match frontend interface
        return data.map(o => ({
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
            pkg: o.pkg || 'Box'
        }));
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
	            // If response is not JSON, throw a generic error
	            throw new Error('Failed to create order');
	        }
	        if (!res.ok) {
	            // Bubble up server-provided error details when available
	            throw data || new Error('Failed to create order');
	        }
	        return data;
	    },

    async assignRider(orderNumber, riderId) {
        const res = await fetch(`${API_BASE_URL}/dispatch/orders/${orderNumber}/assign_rider/`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ rider_id: riderId })
        });
        if (!res.ok) throw new Error('Failed to assign rider');
        return await res.json();
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

