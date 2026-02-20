
const API_BASE_URL = 'https://www.orders.axpress.net/api';

// --- Interfaces ---

export interface User {
  id: number;
  contact_name: string;
  business_name: string;
  phone: string;
  email: string;
  address?: string;
  role?: string;
  [key: string]: any;
}

export interface Tokens {
  access: string;
  refresh: string;
}

export interface AuthResponse {
  success: boolean;
  message?: string;
  tokens?: Tokens;
  user?: User;
  error?: string;
  errors?: any;
  [key: string]: any;
}

export interface Order {
  id: number;
  order_number: string;
  status: string;
  pickup_address: string;
  total_amount: string | number;
  created_at: string;
  vehicle_name: string;
  user_business_name: string;
  deliveries: any[];
  mode: string;
  payment_method: string;
  [key: string]: any;
}

export interface Transaction {
  id: number;
  type: string;
  amount: string | number;
  description: string;
  created_at: string;
  reference: string;
  balance_after: string | number;
  status: string;
}

export interface Vehicle {
    name: string;
    base_fare: number;
    rate_per_km: number;
    rate_per_minute: number;
}

// --- Token Management ---

export const TokenManager = {
  getAccessToken: (): string | null => {
    if (typeof window !== 'undefined') return localStorage.getItem('access_token');
    return null;
  },
  getRefreshToken: (): string | null => {
    if (typeof window !== 'undefined') return localStorage.getItem('refresh_token');
    return null;
  },
  setTokens: (access: string, refresh: string) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
    }
  },
  clearTokens: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  },
  getUser: (): User | null => {
    if (typeof window !== 'undefined') {
      const user = localStorage.getItem('user');
      return user ? JSON.parse(user) : null;
    }
    return null;
  },
  setUser: (user: User) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('user', JSON.stringify(user));
    }
  }
};

// --- Helpers ---

function extractErrorMessage(data: any): string {
  if (data.errors) {
    if (data.errors.non_field_errors && Array.isArray(data.errors.non_field_errors)) {
      return data.errors.non_field_errors[0];
    }
    const firstErrorKey = Object.keys(data.errors)[0];
    if (firstErrorKey) {
      const errorValue = data.errors[firstErrorKey];
      if (Array.isArray(errorValue)) {
        return `${firstErrorKey}: ${errorValue[0]}`;
      }
      return `${firstErrorKey}: ${errorValue}`;
    }
  }
  if (data.message) return data.message;
  if (data.detail) return data.detail;
  return 'Request failed';
}

interface ApiOptions extends RequestInit {
  skipAuth?: boolean;
}

async function apiRequest<T = any>(endpoint: string, options: ApiOptions = {}): Promise<T> {
  const token = TokenManager.getAccessToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token && !options.skipAuth) {
    (headers as any)['Authorization'] = `Bearer ${token}`;
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    
    // Handle 204 No Content
    if (response.status === 204) return { success: true } as any;

    const data = await response.json();

    if (!response.ok) {
      const errorMessage = extractErrorMessage(data);
      throw new Error(errorMessage);
    }

    return data;
  } catch (error) {
    console.error('API Error:', error);
    // Return error structure rather than throwing if prefer handling in UI
    // But original code threw error in some cases, caught in others?
    // The original `api.js` threw new Error(errorMessage).
    throw error;
  }
}

// --- API Modules ---

export const AuthAPI = {
  signup: async (userData: any): Promise<AuthResponse> => {
    const response = await apiRequest<AuthResponse>('/auth/signup/', {
      method: 'POST',
      body: JSON.stringify(userData),
      skipAuth: true,
    });
    if (response.success && response.tokens && response.user) {
      TokenManager.setTokens(response.tokens.access, response.tokens.refresh);
      TokenManager.setUser(response.user);
    }
    return response;
  },

  login: async (phone: string, password: string): Promise<AuthResponse> => {
    const response = await apiRequest<AuthResponse>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ phone, password }),
      skipAuth: true,
    });
    if (response.success && response.tokens && response.user) {
      TokenManager.setTokens(response.tokens.access, response.tokens.refresh);
      TokenManager.setUser(response.user);
    }
    return response;
  },

  logout: async () => {
    try {
      const refreshToken = TokenManager.getRefreshToken();
      await apiRequest('/auth/logout/', {
        method: 'POST',
        body: JSON.stringify({ refresh: refreshToken }),
      });
    } finally {
      TokenManager.clearTokens();
    }
  },

  getProfile: async () => apiRequest('/auth/me/', { method: 'GET' }),

  updateProfile: async (userData: any) => {
    const response = await apiRequest<AuthResponse>('/auth/profile/', {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
    if (response.success && response.user) {
      TokenManager.setUser(response.user);
    }
    return response;
  },

  getAddresses: async () => apiRequest('/auth/addresses/', { method: 'GET' }),
  createAddress: async (addressData: any) => apiRequest('/auth/addresses/', { method: 'POST', body: JSON.stringify(addressData) }),
  updateAddress: async (addressId: number, addressData: any) => apiRequest(`/auth/addresses/${addressId}/`, { method: 'PUT', body: JSON.stringify(addressData) }),
  deleteAddress: async (addressId: number) => apiRequest(`/auth/addresses/${addressId}/`, { method: 'DELETE' }),
  setDefaultAddress: async (addressId: number) => apiRequest(`/auth/addresses/${addressId}/set-default/`, { method: 'POST' }),
};

export const OrdersAPI = {
  getVehicles: async () => apiRequest<{success: boolean, vehicles: Vehicle[]}>('/orders/vehicles/', { method: 'GET' }),
  createQuickSend: async (orderData: any) => apiRequest('/orders/quick-send/', { method: 'POST', body: JSON.stringify(orderData) }),
  createMultiDrop: async (orderData: any) => apiRequest('/orders/multi-drop/', { method: 'POST', body: JSON.stringify(orderData) }),
  createBulkImport: async (orderData: any) => apiRequest('/orders/bulk-import/', { method: 'POST', body: JSON.stringify(orderData) }),
  getOrders: async (filters: any = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.mode) params.append('mode', filters.mode);
    if (filters.limit) params.append('limit', filters.limit);
    const queryString = params.toString();
    const endpoint = queryString ? `/orders/?${queryString}` : '/orders/';
    return await apiRequest(endpoint, { method: 'GET' });
  },
  getOrderDetails: async (orderNumber: string) => apiRequest(`/orders/${orderNumber}/`, { method: 'GET' }),
  getOrderStats: async () => apiRequest('/orders/stats/', { method: 'GET' }),
  cancelOrder: async (orderNumber: string, reason = 'Canceled by merchant') => apiRequest(`/orders/cancel/${orderNumber}/`, { method: 'POST', body: JSON.stringify({ reason }) }),
};

export const WalletAPI = {
  getPaystackKey: async () => apiRequest('/wallet/paystack-key/', { method: 'GET' }),
  getBalance: async () => apiRequest('/wallet/balance/', { method: 'GET' }),
  getTransactions: async (params: any = {}) => {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `/wallet/transactions/?${queryString}` : '/wallet/transactions/';
    return await apiRequest(url, { method: 'GET' });
  },
  initializePayment: async (amount: number) => apiRequest('/wallet/fund/initialize/', { method: 'POST', body: JSON.stringify({ amount: amount.toString() }) }),
  verifyPayment: async (reference: string) => apiRequest('/wallet/fund/verify/', { method: 'POST', body: JSON.stringify({ reference }) }),
};

// Default export matching original usage
const API = {
    Auth: AuthAPI,
    Orders: OrdersAPI,
    Wallet: WalletAPI,
    Token: TokenManager
};

export default API;
