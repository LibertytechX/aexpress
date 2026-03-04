/**
 * API Service for AX Merchant Portal
 * Handles all backend API communication
 */

const API_BASE_URL = window.VITE_API_BASE_URL || 'https://www.orders.axpress.net/api';

// Token management
const TokenManager = {
  getAccessToken: () => localStorage.getItem('access_token'),
  getRefreshToken: () => localStorage.getItem('refresh_token'),
  setTokens: (access, refresh) => {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  },
  clearTokens: () => {
    localStorage.clear();
    sessionStorage.clear();
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
// ────────────────────────────────────────────────────────────────

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
    let response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    let data = await response.json().catch(() => ({}));

    // If unauthorized and we have a refresh token (and we're not already trying to fetch the refresh endpoint), try to refresh
    if (!response.ok && response.status === 401 && !options.skipAuth && endpoint !== '/auth/refresh/') {
      const refreshToken = TokenManager.getRefreshToken();
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
              TokenManager.setTokens(refreshData.access, refreshData.refresh || refreshToken);
              isRefreshing = false;
              onRefreshed(refreshData.access);

              // Retry original request
              config.headers['Authorization'] = `Bearer ${refreshData.access}`;
              response = await fetch(`${API_BASE_URL}${endpoint}`, config);
              data = await response.json().catch(() => ({}));
            } else {
              throw new Error('Refresh failed');
            }
          } catch (refreshErr) {
            isRefreshing = false;
            TokenManager.clearTokens();
            // Optional: trigger a custom event or reload the page to kick the user out visually
            window.dispatchEvent(new Event('auth:unauthorized'));
            throw new Error('Session expired. Please log in again.');
          }
        } else {
          // Wait for the ongoing refresh to complete, then retry
          return new Promise((resolve, reject) => {
            addRefreshSubscriber(async (newToken) => {
              config.headers['Authorization'] = `Bearer ${newToken}`;
              try {
                const retryRes = await fetch(`${API_BASE_URL}${endpoint}`, config);
                const retryData = await retryRes.json().catch(() => ({}));
                if (!retryRes.ok) {
                  return reject(new Error(extractErrorMessage(retryData) || 'Request failed'));
                }
                resolve(retryData);
              } catch (err) {
                reject(err);
              }
            });
          });
        }
      } else {
        // 401 but no refresh token
        TokenManager.clearTokens();
        window.dispatchEvent(new Event('auth:unauthorized'));
      }
    }

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
    // Blacklist the refresh token on the server (best-effort)
    try {
      const refreshToken = TokenManager.getRefreshToken();
      if (refreshToken) {
        await apiRequest('/auth/logout/', {
          method: 'POST',
          body: JSON.stringify({ refresh: refreshToken }),
        });
      }
    } catch (_) { /* always clear locally even if server call fails */ }
    // Wipe all local storage and session storage
    TokenManager.clearTokens();
    // Wipe all browser caches (service workers, fetch cache)
    if ('caches' in window) {
      try {
        const keys = await caches.keys();
        await Promise.all(keys.map(k => caches.delete(k)));
      } catch (_) { }
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

  // Address management
  getAddresses: async () => {
    return await apiRequest('/auth/addresses/', {
      method: 'GET',
    });
  },

  createAddress: async (addressData) => {
    return await apiRequest('/auth/addresses/', {
      method: 'POST',
      body: JSON.stringify(addressData),
    });
  },

  updateAddress: async (addressId, addressData) => {
    return await apiRequest(`/auth/addresses/${addressId}/`, {
      method: 'PUT',
      body: JSON.stringify(addressData),
    });
  },

  deleteAddress: async (addressId) => {
    return await apiRequest(`/auth/addresses/${addressId}/`, {
      method: 'DELETE',
    });
  },

  setDefaultAddress: async (addressId) => {
    return await apiRequest(`/auth/addresses/${addressId}/set-default/`, {
      method: 'POST',
    });
  },

  resendVerification: async () => {
    return await apiRequest('/auth/resend-verification/', {
      method: 'POST',
    });
  },

  requestPasswordReset: async (email) => {
    return await apiRequest('/auth/request-password-reset/', {
      method: 'POST',
      body: JSON.stringify({ email }),
      skipAuth: true,
    });
  },

  resetPassword: async (token, newPassword) => {
    return await apiRequest('/auth/reset-password/', {
      method: 'POST',
      body: JSON.stringify({ token, new_password: newPassword, confirm_password: newPassword }),
      skipAuth: true,
    });
  },

  resendOTP: async (phone) => {
    return await apiRequest("/auth/resend-otp/", {
      method: "POST",
      body: JSON.stringify({ phone }),
      skipAuth: true,
    });
  },

  verifyOTP: async (phone, otp) => {
    return await apiRequest("/auth/verify-otp/", {
      method: "POST",
      body: JSON.stringify({ phone, otp }),
      skipAuth: true,
    });
  },

  verifyEmail: async (token) => {
    return await apiRequest(`/auth/verify-email/?token=${token}`, {
      method: 'GET',
      skipAuth: true,
    });
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

  /**
   * Get (or create) the merchant's CoreBanking virtual account.
   * Returns account_number, account_name, bank_name, bank_code.
   */
  getVirtualAccount: async () => {
    return await apiRequest('/wallet/virtual-account/', {
      method: 'GET',
    });
  },

  /**
   * Record that the merchant has claimed to have made a bank transfer.
   * Creates a pending transaction so the claim is audited.
   * The actual wallet credit happens when the bank webhook confirms the transfer.
   * @param {number} amount - Amount in Naira
   */
  claimTransfer: async (amount) => {
    return await apiRequest('/wallet/fund/transfer-claim/', {
      method: 'POST',
      body: JSON.stringify({ amount: amount.toString() }),
    });
  },
};

// Activity / Ably API
const ActivityAPI = {
  /**
   * Request an Ably token from the backend.
   * The returned object contains { token, token_request } and can be
   * passed directly to Ably's authCallback.
   */
  getAblyToken: async () => {
    return await apiRequest('/dispatch/ably-token/', { method: 'GET' });
  },
};

// Export API modules
window.API = {
  Auth: AuthAPI,
  Orders: OrdersAPI,
  Wallet: WalletAPI,
  Activity: ActivityAPI,
  Token: TokenManager,
};

