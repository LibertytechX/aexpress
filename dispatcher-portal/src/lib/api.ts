// API Service for Dispatcher Portal (Next.js)
// Set NEXT_PUBLIC_API_BASE_URL in .env.local for local dev; defaults to production.
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://www.orders.axpress.net/api';

// ─── TOKEN HELPERS ──────────────────────────────────────────────
const getToken = (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
};

const authHeaders = (customHeaders: Record<string, string> = {}): HeadersInit => {
    const token = getToken();
    return {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...customHeaders,
    };
};

// ─── AUTO-REFRESH LOGIC ─────────────────────────────────────────
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function onRefreshed(token: string) {
    refreshSubscribers.forEach(cb => cb(token));
    refreshSubscribers = [];
}

function addRefreshSubscriber(cb: (token: string) => void) {
    refreshSubscribers.push(cb);
}

// ─── CENTRALIZED AUTH FETCH ─────────────────────────────────────
export async function fetchWithAuth(endpoint: string, options: RequestInit = {}): Promise<Response> {
    const isFormData = options.body instanceof FormData;
    const defaultHeaders: Record<string, string> = isFormData ? {} : { 'Content-Type': 'application/json' };
    const baseHeaders: Record<string, string> = { ...defaultHeaders, ...(options.headers as Record<string, string> || {}) };

    const token = getToken();
    if (token) baseHeaders['Authorization'] = `Bearer ${token}`;

    const config: RequestInit = { ...options, headers: baseHeaders };
    let res = await fetch(`${API_BASE_URL}${endpoint}`, config);

    if (!res.ok && res.status === 401) {
        const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;
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
                        (config.headers as Record<string, string>)['Authorization'] = `Bearer ${refreshData.access}`;
                        res = await fetch(`${API_BASE_URL}${endpoint}`, config);
                    } else {
                        throw new Error('Refresh failed');
                    }
                } catch (err) {
                    isRefreshing = false;
                    if (typeof window !== 'undefined') {
                        localStorage.clear();
                        sessionStorage.clear();
                        window.dispatchEvent(new Event('auth:unauthorized'));
                    }
                    throw err;
                }
            } else {
                return new Promise<Response>((resolve, reject) => {
                    addRefreshSubscriber(async (newToken: string) => {
                        (config.headers as Record<string, string>)['Authorization'] = `Bearer ${newToken}`;
                        try {
                            resolve(await fetch(`${API_BASE_URL}${endpoint}`, config));
                        } catch (err) {
                            reject(err);
                        }
                    });
                });
            }
        } else {
            if (typeof window !== 'undefined') {
                localStorage.clear();
                sessionStorage.clear();
                window.dispatchEvent(new Event('auth:unauthorized'));
            }
        }
    }

    return res;
}

// ─── AUTHENTICATION ─────────────────────────────────────────────
export const AuthAPI = {
    async login(phone: string, password: string) {
        const res = await fetch(`${API_BASE_URL}/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, password }),
        });
        const data = await res.json();
        if (!res.ok) throw data;
        const tokens = data.tokens || data;
        if (tokens.access) localStorage.setItem('access_token', tokens.access);
        if (tokens.refresh) localStorage.setItem('refresh_token', tokens.refresh);
        return data;
    },

    async logout() {
        try {
            const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;
            if (refreshToken) {
                await fetchWithAuth(`/auth/logout/`, {
                    method: 'POST',
                    body: JSON.stringify({ refresh_token: refreshToken }),
                });
            }
        } catch (_) { /* always clear locally */ }
        if (typeof window !== 'undefined') {
            localStorage.clear();
            sessionStorage.clear();
            if ('caches' in window) {
                try {
                    const keys = await caches.keys();
                    await Promise.all(keys.map(k => caches.delete(k)));
                } catch (_) { }
            }
        }
    },

    isAuthenticated(): boolean {
        return !!getToken();
    },

    async requestPasswordReset(email: string) {
        const res = await fetch(`${API_BASE_URL}/auth/request-password-reset/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email }),
        });
        const data = await res.json();
        if (!res.ok) throw data;
        return data;
    },

    async resetPassword(token: string, newPassword: string) {
        const res = await fetch(`${API_BASE_URL}/auth/reset-password/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, new_password: newPassword, confirm_password: newPassword }),
        });
        const data = await res.json();
        if (!res.ok) throw data;
        return data;
    },
};

// ─── RIDERS ─────────────────────────────────────────────────────
export const RidersAPI = {
    async getAll() {
        const res = await fetchWithAuth(`/dispatch/riders/`);
        if (!res.ok) throw new Error('Failed to fetch riders');
        const data = await res.json();
        return data.map((r: any) => ({
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
            _uuid: r.id,
        }));
    },

    async createRider(fields: Record<string, any>) {
        const form = new FormData();
        Object.entries(fields).forEach(([k, v]) => {
            if (v !== null && v !== undefined && v !== '') form.append(k, v);
        });
        const res = await fetchWithAuth(`/dispatch/riders/onboarding/`, { method: 'POST', body: form });
        const data = await res.json();
        if (!res.ok) throw data;
        return data;
    },

    async resetPassword(riderUuid: string, newPassword: string) {
        const res = await fetchWithAuth(`/dispatch/riders/${riderUuid}/reset_password/`, {
            method: 'POST',
            body: JSON.stringify({ new_password: newPassword }),
        });
        const data = await res.json();
        if (!res.ok) throw data;
        return data;
    },

    async assignVehicle(riderUuid: string, vehicleAssetId: string | null) {
        const res = await fetchWithAuth(`/dispatch/riders/${riderUuid}/assign_vehicle/`, {
            method: 'POST',
            body: JSON.stringify({ vehicle_asset_id: vehicleAssetId || null }),
        });
        const data = await res.json();
        if (!res.ok) throw data;
        return data;
    },

    async toggleDuty(riderUuid: string, status: string) {
        const res = await fetchWithAuth(`/dispatch/riders/${riderUuid}/toggle_duty/`, {
            method: 'POST',
            body: JSON.stringify({ status }),
        });
        const data = await res.json();
        if (!res.ok) throw data;
        return data;
    },
};

// ─── ORDERS ─────────────────────────────────────────────────────
const normalizeOrder = (o: any) => ({
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

    async getOne(orderNumber: string) {
        const res = await fetchWithAuth(`/dispatch/orders/${orderNumber}/`);
        if (!res.ok) throw new Error('Failed to fetch order');
        return normalizeOrder(await res.json());
    },

    async create(orderData: any) {
        const res = await fetchWithAuth(`/dispatch/orders/`, {
            method: 'POST',
            body: JSON.stringify(orderData),
        });
        const data = await res.json().catch(() => { throw new Error('Failed to create order'); });
        if (!res.ok) throw data || new Error('Failed to create order');
        return normalizeOrder(data);
    },

    async assignRider(orderNumber: string, riderId: string) {
        const res = await fetchWithAuth(`/dispatch/orders/${orderNumber}/assign_rider/`, {
            method: 'POST',
            body: JSON.stringify({ rider_id: riderId }),
        });
        if (!res.ok) throw new Error('Failed to assign rider');
        return await res.json();
    },

    async updateStatus(orderNumber: string, newStatus: string) {
        const res = await fetchWithAuth(`/dispatch/orders/${orderNumber}/update_status/`, {
            method: 'POST',
            body: JSON.stringify({ status: newStatus }),
        });
        if (!res.ok) throw new Error('Failed to update status');
        return await res.json();
    },

    async updatePrice(orderNumber: string, amount: number) {
        const res = await fetchWithAuth(`/dispatch/orders/${orderNumber}/update-price/`, {
            method: 'PATCH',
            body: JSON.stringify({ amount }),
        });
        const data = await res.json().catch(() => null);
        if (!res.ok) throw data || new Error('Failed to update price');
        return normalizeOrder(data);
    },

    async generateRelayRoute(orderNumber: string, force = false) {
        const res = await fetchWithAuth(`/dispatch/orders/${orderNumber}/generate-relay-route/`, {
            method: 'POST',
            body: JSON.stringify({ force }),
        });
        const data = await res.json().catch(() => { throw new Error('Failed to generate relay route'); });
        if (!res.ok) throw data || new Error('Failed to generate relay route');
        return normalizeOrder(data);
    },
};

// ─── MERCHANTS ──────────────────────────────────────────────────
export const MerchantsAPI = {
    async getAll() {
        const res = await fetchWithAuth(`/dispatch/merchants/`);
        if (!res.ok) throw new Error('Failed to fetch merchants');
        const data = await res.json();
        return data.map((m: any) => ({
            id: m.id || 'N/A',
            userId: m.userId || m.user_id || m.user || null,
            name: m.name || 'Unknown',
            contact: m.contact || '',
            phone: m.phone || '',
            category: m.category || 'General',
            totalOrders: m.totalOrders || 0,
            monthOrders: m.monthOrders || 0,
            walletBalance: parseFloat(m.walletBalance) || 0,
            status: m.status || 'Active',
            joined: m.joined || 'N/A',
        }));
    },
};

// ─── MERCHANT PRICING OVERRIDES ─────────────────────────────────
export const MerchantPricingOverridesAPI = {
    async list({ merchant, vehicle, active }: { merchant?: string; vehicle?: string; active?: boolean } = {}) {
        const qs = new URLSearchParams();
        if (merchant) qs.set('merchant', merchant);
        if (vehicle) qs.set('vehicle', vehicle);
        if (active !== undefined) qs.set('active', String(active));
        const res = await fetchWithAuth(`/dispatch/merchant-pricing-overrides/${qs.toString() ? `?${qs.toString()}` : ''}`);
        const data = await res.json().catch(() => null);
        if (!res.ok) throw data || new Error('Failed to fetch merchant pricing overrides');
        return Array.isArray(data) ? data : (data?.results || []);
    },

    async upsert(payload: any) {
        const res = await fetchWithAuth(`/dispatch/merchant-pricing-overrides/`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        const data = await res.json().catch(() => null);
        if (!res.ok) throw data || new Error('Failed to save merchant pricing override');
        return data;
    },

    async remove(id: string) {
        const res = await fetchWithAuth(`/dispatch/merchant-pricing-overrides/${id}/`, { method: 'DELETE' });
        if (!res.ok) {
            const data = await res.json().catch(() => null);
            throw data || new Error('Failed to delete merchant pricing override');
        }
        return true;
    },
};

// ─── VEHICLES ───────────────────────────────────────────────────
export const VehiclesAPI = {
    async getAll() {
        const res = await fetchWithAuth(`/orders/vehicles/`);
        if (!res.ok) throw new Error('Failed to fetch vehicles');
        const data = await res.json();
        return Array.isArray(data) ? data : (data.vehicles || []);
    },

    async update(id: string, data: any) {
        const res = await fetchWithAuth(`/orders/vehicles/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error('Failed to update vehicle');
        return await res.json();
    },
};

// ─── VEHICLE ASSETS ─────────────────────────────────────────────
export const VehicleAssetsAPI = {
    async getAll() {
        const res = await fetchWithAuth(`/dispatch/vehicle-assets/`);
        if (!res.ok) throw new Error('Failed to fetch vehicle assets');
        return await res.json();
    },

    async create(data: any) {
        const res = await fetchWithAuth(`/dispatch/vehicle-assets/`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
        if (!res.ok) throw await res.json().catch(() => new Error('Failed to create vehicle asset'));
        return await res.json();
    },

    async update(id: string, data: any) {
        const res = await fetchWithAuth(`/dispatch/vehicle-assets/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error('Failed to update vehicle asset');
        return await res.json();
    },

    async delete(id: string) {
        const res = await fetchWithAuth(`/dispatch/vehicle-assets/${id}/`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete vehicle asset');
    },
};

// ─── ACTIVITY FEED ──────────────────────────────────────────────
export const ActivityFeedAPI = {
    async getRecent(limit = 50): Promise<any[]> {
        const res = await fetchWithAuth(`/dispatch/activity/?limit=${limit}`);
        if (!res.ok) throw new Error('Failed to fetch activity feed');
        return await res.json();
    },

    async getAblyToken(): Promise<any> {
        const res = await fetchWithAuth(`/dispatch/ably-token/`);
        if (!res.ok) throw new Error('Failed to get Ably token');
        return await res.json();
    },
};

// ─── SETTINGS ───────────────────────────────────────────────────
export const SettingsAPI = {
    async get() {
        const res = await fetchWithAuth(`/dispatch/settings/`);
        if (!res.ok) throw new Error('Failed to fetch settings');
        return await res.json();
    },

    async update(settings: any) {
        const res = await fetchWithAuth(`/dispatch/settings/`, {
            method: 'POST',
            body: JSON.stringify(settings),
        });
        if (!res.ok) throw new Error('Failed to update settings');
        return await res.json();
    },
};

// ─── ZONES ──────────────────────────────────────────────────────
export const ZonesAPI = {
    async getAll() {
        const res = await fetchWithAuth(`/dispatch/zones/`);
        if (!res.ok) throw new Error('Failed to fetch zones');
        const data = await res.json();
        return Array.isArray(data) ? data : (data.results || []);
    },

    async create(zone: any) {
        const res = await fetchWithAuth(`/dispatch/zones/`, {
            method: 'POST',
            body: JSON.stringify(zone),
        });
        if (!res.ok) throw new Error('Failed to create zone');
        return await res.json();
    },

    async update(id: string, zone: any) {
        const res = await fetchWithAuth(`/dispatch/zones/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(zone),
        });
        if (!res.ok) throw new Error('Failed to update zone');
        return await res.json();
    },

    async remove(id: string) {
        const res = await fetchWithAuth(`/dispatch/zones/${id}/`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete zone');
    },
};

// ─── RELAY NODES ─────────────────────────────────────────────────
export const RelayNodesAPI = {
    async getAll() {
        const res = await fetchWithAuth(`/dispatch/relay-nodes/`);
        if (!res.ok) throw new Error('Failed to fetch relay nodes');
        const data = await res.json();
        return Array.isArray(data) ? data : (data.results || []);
    },

    async create(node: any) {
        const res = await fetchWithAuth(`/dispatch/relay-nodes/`, {
            method: 'POST',
            body: JSON.stringify(node),
        });
        if (!res.ok) throw new Error('Failed to create relay node');
        return await res.json();
    },

    async update(id: string, node: any) {
        const res = await fetchWithAuth(`/dispatch/relay-nodes/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(node),
        });
        if (!res.ok) throw new Error('Failed to update relay node');
        return await res.json();
    },

    async remove(id: string) {
        const res = await fetchWithAuth(`/dispatch/relay-nodes/${id}/`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete relay node');
    },
};

// ─── DISPATCHERS ─────────────────────────────────────────────────
export const DispatchersAPI = {
    async getAll() {
        const res = await fetchWithAuth(`/dispatch/dispatchers/`);
        if (!res.ok) throw new Error('Failed to fetch dispatchers');
        return await res.json();
    },

    async create(fields: any) {
        const res = await fetchWithAuth(`/dispatch/dispatchers/`, {
            method: 'POST',
            body: JSON.stringify(fields),
        });
        const data = await res.json();
        if (!res.ok) throw data;
        return data;
    },
};
