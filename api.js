/**
 * API Service for AX Merchant Portal
 * Handles all backend API communication
 */

const API_BASE_URL = 'https://www.orders.axpress.net/api';

// Token management
const TokenManager = {
  getAccessToken: () => localStorage.getItem('access_token'),
  getRefreshToken: () => localStorage.getItem('refresh_token'),
  setTokens: (access, refresh) => {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  },
  clearTokens: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },
  getUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },
  setUser: (user) => {
    localStorage.setItem('user', JSON.stringify(user));
  }
};

// Helper to extract error message from API response
function extractErrorMessage(data) {
  // Check for errors object (Django REST Framework format)
  if (data.errors) {
    // Handle non_field_errors
    if (data.errors.non_field_errors && Array.isArray(data.errors.non_field_errors)) {
      return data.errors.non_field_errors[0];
    }

    // Handle field-specific errors
    const firstErrorKey = Object.keys(data.errors)[0];
    if (firstErrorKey) {
      const errorValue = data.errors[firstErrorKey];
      if (Array.isArray(errorValue)) {
        return `${firstErrorKey}: ${errorValue[0]}`;
      }
      return `${firstErrorKey}: ${errorValue}`;
    }
  }

  // Check for message field
  if (data.message) {
    return data.message;
  }

  // Check for detail field (DRF default)
  if (data.detail) {
    return data.detail;
  }

  // Fallback
  return 'Request failed';
}

// API request helper
async function apiRequest(endpoint, options = {}) {
  const token = TokenManager.getAccessToken();

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token && !options.skipAuth) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    const data = await response.json();

    if (!response.ok) {
      const errorMessage = extractErrorMessage(data);
      throw new Error(errorMessage);
    }

    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

// Authentication API
const AuthAPI = {
  signup: async (userData) => {
    const response = await apiRequest('/auth/signup/', {
      method: 'POST',
      body: JSON.stringify(userData),
      skipAuth: true,
    });

    if (response.success && response.tokens) {
      TokenManager.setTokens(response.tokens.access, response.tokens.refresh);
      TokenManager.setUser(response.user);
    }

    return response;
  },

  login: async (phone, password) => {
    const response = await apiRequest('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ phone, password }),
      skipAuth: true,
    });

    if (response.success && response.tokens) {
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

  getProfile: async () => {
    return await apiRequest('/auth/me/', {
      method: 'GET',
    });
  },

  updateProfile: async (userData) => {
    const response = await apiRequest('/auth/profile/', {
      method: 'PUT',
      body: JSON.stringify(userData),
    });

    // Update user in localStorage if successful
    if (response.success && response.user) {
      TokenManager.setUser(response.user);
    }

    return response;
  },
};

// Orders API
const OrdersAPI = {
  getVehicles: async () => {
    return await apiRequest('/orders/vehicles/', {
      method: 'GET',
    });
  },

  createQuickSend: async (orderData) => {
    return await apiRequest('/orders/quick-send/', {
      method: 'POST',
      body: JSON.stringify(orderData),
    });
  },

  createMultiDrop: async (orderData) => {
    return await apiRequest('/orders/multi-drop/', {
      method: 'POST',
      body: JSON.stringify(orderData),
    });
  },

  createBulkImport: async (orderData) => {
    return await apiRequest('/orders/bulk-import/', {
      method: 'POST',
      body: JSON.stringify(orderData),
    });
  },

  getOrders: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.mode) params.append('mode', filters.mode);
    if (filters.limit) params.append('limit', filters.limit);

    const queryString = params.toString();
    const endpoint = queryString ? `/orders/?${queryString}` : '/orders/';

    return await apiRequest(endpoint, {
      method: 'GET',
    });
  },

  getOrderDetails: async (orderNumber) => {
    return await apiRequest(`/orders/${orderNumber}/`, {
      method: 'GET',
    });
  },

  getOrderStats: async () => {
    return await apiRequest('/orders/stats/', {
      method: 'GET',
    });
  },

  cancelOrder: async (orderNumber, reason = 'Canceled by merchant') => {
    return await apiRequest(`/orders/cancel/${orderNumber}/`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },
};

// Wallet API
const WalletAPI = {
  /**
   * Get Paystack public key
   */
  getPaystackKey: async () => {
    return await apiRequest('/wallet/paystack-key/', {
      method: 'GET',
    });
  },

  /**
   * Get wallet balance
   */
  getBalance: async () => {
    return await apiRequest('/wallet/balance/', {
      method: 'GET',
    });
  },

  /**
   * Get transaction history
   * @param {Object} params - Query parameters (type, status, page)
   */
  getTransactions: async (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `/wallet/transactions/?${queryString}` : '/wallet/transactions/';
    return await apiRequest(url, {
      method: 'GET',
    });
  },

  /**
   * Initialize Paystack payment for wallet funding
   * @param {number} amount - Amount to fund in Naira
   */
  initializePayment: async (amount) => {
    return await apiRequest('/wallet/fund/initialize/', {
      method: 'POST',
      body: JSON.stringify({ amount: amount.toString() }),
    });
  },

  /**
   * Verify Paystack payment
   * @param {string} reference - Paystack payment reference
   */
  verifyPayment: async (reference) => {
    return await apiRequest('/wallet/fund/verify/', {
      method: 'POST',
      body: JSON.stringify({ reference }),
    });
  },
};

// Export API modules
window.API = {
  Auth: AuthAPI,
  Orders: OrdersAPI,
  Wallet: WalletAPI,
  Token: TokenManager,
};

