// API Service for Dispatcher Frontend
// In dev: create dispatcher-frontend/.env.local with VITE_API_BASE_URL=http://localhost:8000/api
// In prod: the default .env value (production server) is used automatically
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://www.orders.axpress.net/api';

// Get stored auth token
const getToken = () => localStorage.getItem('access_token');

// Helper for authenticated requests
const authHeaders = (customHeaders = {}) => {
    const token = getToken();
    return {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...customHeaders
    };
};

// ─── AUTO-REFRESH LOGIC ─────────────────────────────────────────
let isRefreshing = false;
let refreshSubscribers = [];

function onRefreshed(token) {
    refreshSubscribers.forEach((callback) => callback(token));
    refreshSubscribers = [];
}

function addRefreshSubscriber(callback) {
    refreshSubscribers.push(callback);
}

// ─── CENTRALIZED AUTH FETCH ─────────────────────────────────────
export async function fetchWithAuth(endpoint, options = {}) {
    // Determine headers. If passing FormData, browser sets multipart/form-data boundary automatically, so omit Content-Type.
    const isFormData = options.body instanceof FormData;
    const defaultHeaders = isFormData ? {} : { 'Content-Type': 'application/json' };
    const baseHeaders = { ...defaultHeaders, ...options.headers };

    // Inject auth token
    const token = getToken();
    if (token) baseHeaders['Authorization'] = `Bearer ${token}`;

    const config = { ...options, headers: baseHeaders };

    // Initial fetch
    let res = await fetch(`${API_BASE_URL}${endpoint}`, config);

    // If 401 Unauthorized, attempt refresh
    if (!res.ok && res.status === 401) {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            if (!isRefreshing) {
                isRefreshing = true;
                try {
                    const refreshRes = await fetch(`${API_BASE_URL}/auth/refresh/`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ refresh: refreshToken }),
                    });
                    const refreshData = await refreshRes.json();

                    if (refreshRes.ok && refreshData.access) {
                        localStorage.setItem('access_token', refreshData.access);
                        if (refreshData.refresh) localStorage.setItem('refresh_token', refreshData.refresh);

                        isRefreshing = false;
                        onRefreshed(refreshData.access);

                        // Retry original request
                        config.headers['Authorization'] = `Bearer ${refreshData.access}`;
                        res = await fetch(`${API_BASE_URL}${endpoint}`, config);
                    } else {
                        throw new Error('Refresh failed');
                    }
                } catch (refreshErr) {
                    isRefreshing = false;
                    localStorage.clear();
                    sessionStorage.clear();
                    window.dispatchEvent(new Event('auth:unauthorized'));
                    throw refreshErr;
                }
            } else {
                // Wait for ongoing refresh
                return new Promise((resolve, reject) => {
                    addRefreshSubscriber(async (newToken) => {
                        config.headers['Authorization'] = `Bearer ${newToken}`;
                        try {
                            const retryRes = await fetch(`${API_BASE_URL}${endpoint}`, config);
                            resolve(retryRes);
                        } catch (err) {
                            reject(err);
                        }
                    });
                });
            }
        } else {
            // 401 but no refresh token
            localStorage.clear();
            sessionStorage.clear();
            window.dispatchEvent(new Event('auth:unauthorized'));
        }
    }

    return res;
}

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

    async logout() {
        // Blacklist the refresh token on the server (best-effort)
        try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
                await fetchWithAuth(`/auth/logout/`, {
                    method: 'POST',
                    body: JSON.stringify({ refresh_token: refreshToken })
                });
            }
        } catch (_) { /* always clear locally even if server call fails */ }
        // Wipe all local storage and session storage
        localStorage.clear();
        sessionStorage.clear();
        // Wipe all browser caches (service workers, fetch cache)
        if ('caches' in window) {
            try {
                const keys = await caches.keys();
                await Promise.all(keys.map(k => caches.delete(k)));
            } catch (_) { }
        }
    },

    isAuthenticated() {
        return !!getToken();
    },

    async requestPasswordReset(email) {
        const res = await fetch(`${API_BASE_URL}/auth/request-password-reset/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await res.json();
        if (!res.ok) throw data;
        return data;
    },

    async resetPassword(token, newPassword) {
        const res = await fetch(`${API_BASE_URL}/auth/reset-password/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, new_password: newPassword, confirm_password: newPassword })
        });
        const data = await res.json();
        if (!res.ok) throw data;
        return data;
    }
};

// ─── RIDERS ─────────────────────────────────────────────────────
export const RidersAPI = {
    async getAll() {
        const res = await fetchWithAuth(`/dispatch/riders/`);
        if (!res.ok) throw new Error('Failed to fetch riders');
        const data = await res.json();
        // Transform backend data to match frontend interface
        return data.map(r => ({
            id: r.rider_id || r.id,
            name: r.name || 'Unknown',
            phone: r.phone || '',
            vehicle: r.vehicle || 'Bike',
            vehicle_asset: r.vehicle_asset_detail || null,
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
        const res = await fetchWithAuth(`/dispatch/riders/${riderUuid}/update_location/`, {
            method: 'PATCH',
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
        const res = await fetchWithAuth(`/dispatch/riders/onboarding/`, {
            method: 'POST',
            body: form
        });
        const data = await res.json();
        if (!res.ok) throw data;
        return data;
    },

    async resetPassword(riderUuid, newPassword) {
        const res = await fetchWithAuth(`/dispatch/riders/${riderUuid}/reset_password/`, {
            method: 'POST',
            body: JSON.stringify({ new_password: newPassword }),
        });
        const data = await res.json();
        if (!res.ok) throw data;
        return data;
    },

    async assignVehicle(riderUuid, vehicleAssetId) {
        const res = await fetchWithAuth(`/dispatch/riders/${riderUuid}/assign_vehicle/`, {
            method: 'POST',
            body: JSON.stringify({ vehicle_asset_id: vehicleAssetId || null }),
        });
        const data = await res.json();
        if (!res.ok) throw data;
        return data;
    },

    async toggleDuty(riderUuid, status) {
        const res = await fetchWithAuth(`/dispatch/riders/${riderUuid}/toggle_duty/`, {
            method: 'POST',
            body: JSON.stringify({ status }),
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
        const res = await fetchWithAuth(`/dispatch/orders/`);
        if (!res.ok) throw new Error('Failed to fetch orders');
        const data = await res.json();
        return data.map(normalizeOrder);
    },

    async getOne(orderNumber) {
        const res = await fetchWithAuth(`/dispatch/orders/${orderNumber}/`);
        if (!res.ok) throw new Error('Failed to fetch order');
        const data = await res.json();
        return normalizeOrder(data);
    },

    async updatePrice(orderNumber, amount) {
        const res = await fetchWithAuth(`/dispatch/orders/${orderNumber}/update-price/`, {
            method: 'PATCH',
            body: JSON.stringify({ amount })
        });
        let data;
        try { data = await res.json(); } catch (_) { data = null; }
        if (!res.ok) throw (data || new Error('Failed to update price'));
        return normalizeOrder(data);
    },

    async create(orderData) {
        const res = await fetchWithAuth(`/dispatch/orders/`, {
            method: 'POST',
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
        const res = await fetchWithAuth(`/dispatch/orders/${orderNumber}/assign_rider/`, {
            method: 'POST',
            body: JSON.stringify({ rider_id: riderId })
        });
        if (!res.ok) throw new Error('Failed to assign rider');
        return await res.json();
    },

    async updateStatus(orderNumber, newStatus) {
        const res = await fetchWithAuth(`/dispatch/orders/${orderNumber}/update_status/`, {
            method: 'POST',
            body: JSON.stringify({ status: newStatus })
        });
        if (!res.ok) throw new Error('Failed to update status');
        return await res.json();
    },

    async generateRelayRoute(orderNumber, force = false) {
        const res = await fetchWithAuth(`/dispatch/orders/${orderNumber}/generate-relay-route/`, {
            method: 'POST',
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
        const res = await fetchWithAuth(`/dispatch/merchants/`);
        if (!res.ok) throw new Error('Failed to fetch merchants');
        const data = await res.json();
        return data.map(m => ({
            id: m.id || 'N/A',
            // Backend exposes the merchant's UUID as userId; we need it for per-merchant override endpoints.
            userId: m.userId || m.user_id || m.user || null,
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

// ─── MERCHANT PRICING OVERRIDES ─────────────────────────────────
export const MerchantPricingOverridesAPI = {
    async list({ merchant, vehicle, active } = {}) {
        const qs = new URLSearchParams();
        if (merchant) qs.set('merchant', merchant);
        if (vehicle) qs.set('vehicle', vehicle);
        if (active !== undefined && active !== null) qs.set('active', String(active));
        const url = `${API_BASE_URL}/dispatch/merchant-pricing-overrides/${qs.toString() ? `?${qs.toString()}` : ''}`;
        const res = await fetch(url, { headers: authHeaders() });
        let data;
        try { data = await res.json(); } catch (_) { data = null; }
        if (!res.ok) throw (data || new Error('Failed to fetch merchant pricing overrides'));
        return Array.isArray(data) ? data : (data?.results || []);
    },

    async upsert(payload) {
        const res = await fetch(`${API_BASE_URL}/dispatch/merchant-pricing-overrides/`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(payload)
        });
        let data;
        try { data = await res.json(); } catch (_) { data = null; }
        if (!res.ok) throw (data || new Error('Failed to save merchant pricing override'));
        return data;
    },

    async remove(id) {
        const res = await fetch(`${API_BASE_URL}/dispatch/merchant-pricing-overrides/${id}/`, {
            method: 'DELETE',
            headers: authHeaders()
        });
        if (!res.ok) {
            let data;
            try { data = await res.json(); } catch (_) { data = null; }
            throw (data || new Error('Failed to delete merchant pricing override'));
        }
        return true;
    }
};

// ─── VEHICLES ───────────────────────────────────────────────────
export const VehiclesAPI = {
    async getAll() {
        const res = await fetchWithAuth(`/orders/vehicles/`);
        if (!res.ok) throw new Error('Failed to fetch vehicles');
        const data = await res.json();
        // Response shape is { success: true, vehicles: [...] }
        return Array.isArray(data) ? data : (data.vehicles || []);
    },

    async update(id, data) {
        const res = await fetchWithAuth(`/orders/vehicles/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('Failed to update vehicle');
        return await res.json();
    }
};

// ─── VEHICLE ASSETS ─────────────────────────────────────────────
export const VehicleAssetsAPI = {
    async getAll() {
        const res = await fetchWithAuth(`/dispatch/vehicle-assets/`);
        if (!res.ok) throw new Error('Failed to fetch vehicle assets');
        return await res.json();
    },

    async get(id) {
        const res = await fetchWithAuth(`/dispatch/vehicle-assets/${id}/`);
        if (!res.ok) throw new Error('Failed to fetch vehicle asset');
        return await res.json();
    },

    async create(data) {
        const res = await fetchWithAuth(`/dispatch/vehicle-assets/`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw err;
        }
        return await res.json();
    },

    async update(id, data) {
        const res = await fetchWithAuth(`/dispatch/vehicle-assets/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('Failed to update vehicle asset');
        return await res.json();
    },

    async delete(id) {
        const res = await fetchWithAuth(`/dispatch/vehicle-assets/${id}/`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error('Failed to delete vehicle asset');
    }
};

// ─── ACTIVITY FEED ──────────────────────────────────────────────
export const ActivityFeedAPI = {
    async getRecent(limit = 50) {
        const res = await fetchWithAuth(`/dispatch/activity/?limit=${limit}`);
        if (!res.ok) throw new Error('Failed to fetch activity feed');
        return await res.json();
    },

    async getAblyToken() {
        const res = await fetchWithAuth(`/dispatch/ably-token/`);
        if (!res.ok) throw new Error('Failed to get Ably token');
        return await res.json();
    }
};

// ─── SETTINGS ───────────────────────────────────────────────────
export const SettingsAPI = {
    async get() {
        const res = await fetchWithAuth(`/dispatch/settings/`);
        if (!res.ok) throw new Error('Failed to fetch settings');
        return await res.json();
    },

    async update(settings) {
        const res = await fetchWithAuth(`/dispatch/settings/`, {
            method: 'POST',
            body: JSON.stringify(settings)
        });
        if (!res.ok) throw new Error('Failed to update settings');
        return await res.json();
    }
};

// ─── ZONES ──────────────────────────────────────────────────────
export const ZonesAPI = {
    async getAll() {
        const res = await fetchWithAuth(`/dispatch/zones/`);
        if (!res.ok) throw new Error('Failed to fetch zones');
        const data = await res.json();
        return Array.isArray(data) ? data : (data.results || []);
    },

    async create(zone) {
        const res = await fetchWithAuth(`/dispatch/zones/`, {
            method: 'POST',
            body: JSON.stringify(zone)
        });
        if (!res.ok) throw new Error('Failed to create zone');
        return await res.json();
    },

    async update(id, zone) {
        const res = await fetchWithAuth(`/dispatch/zones/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(zone)
        });
        if (!res.ok) throw new Error('Failed to update zone');
        return await res.json();
    },

    async remove(id) {
        const res = await fetchWithAuth(`/dispatch/zones/${id}/`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error('Failed to delete zone');
    }
};

// ─── RELAY NODES ─────────────────────────────────────────────────
export const RelayNodesAPI = {
    async getAll() {
        const res = await fetchWithAuth(`/dispatch/relay-nodes/`);
        if (!res.ok) throw new Error('Failed to fetch relay nodes');
        const data = await res.json();
        return Array.isArray(data) ? data : (data.results || []);
    },

    async create(node) {
        const res = await fetchWithAuth(`/dispatch/relay-nodes/`, {
            method: 'POST',
            body: JSON.stringify(node)
        });
        if (!res.ok) throw new Error('Failed to create relay node');
        return await res.json();
    },

    async update(id, node) {
        const res = await fetchWithAuth(`/dispatch/relay-nodes/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(node)
        });
        if (!res.ok) throw new Error('Failed to update relay node');
        return await res.json();
    },

    async remove(id) {
        const res = await fetchWithAuth(`/dispatch/relay-nodes/${id}/`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error('Failed to delete relay node');
    }
};

// ─── DISPATCHERS ─────────────────────────────────────────────────
export const DispatchersAPI = {
    async getAll() {
        const res = await fetchWithAuth(`/dispatch/dispatchers/`);
        if (!res.ok) throw new Error('Failed to fetch dispatchers');
        return await res.json();
    },

    async create(fields) {
        const res = await fetchWithAuth(`/dispatch/dispatchers/`, {
            method: 'POST',
            body: JSON.stringify(fields)
        });
        const data = await res.json();
        if (!res.ok) throw data;
        return data;
    }
};


