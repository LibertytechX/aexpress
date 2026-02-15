# Frontend-Backend Integration Guide

## Overview

This guide explains how to integrate the MerchantPortal.jsx frontend with the Django backend API.

---

## Changes Required

### 1. API Service (✅ COMPLETED)

Created `frontend/api.js` with:
- Token management (localStorage)
- Authentication API methods
- Orders API methods
- Error handling

### 2. Update MerchantPortal.jsx

The following components need to be updated to use the real API:

#### A. Main App State Management
**Current:** Uses MOCK_ORDERS and MOCK_TRANSACTIONS
**Update:** Fetch from API on component mount

```javascript
// Add useEffect to load data
useEffect(() => {
  const loadData = async () => {
    try {
      // Check if user is logged in
      const user = API.Token.getUser();
      if (!user) {
        setScreen('login');
        return;
      }
      
      // Load orders
      const ordersResponse = await API.Orders.getOrders();
      if (ordersResponse.success) {
        setOrders(transformOrders(ordersResponse.orders));
      }
      
      // Load stats
      const statsResponse = await API.Orders.getOrderStats();
      if (statsResponse.success) {
        // Update dashboard stats
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };
  
  if (screen === 'dashboard') {
    loadData();
  }
}, [screen]);
```

#### B. LoginScreen Component
**Current:** Calls `onLogin()` directly
**Update:** Call API.Auth.login()

```javascript
const handleLogin = async () => {
  try {
    setLoading(true);
    setError('');
    
    const response = await API.Auth.login(phone, pass);
    
    if (response.success) {
      onLogin(response.user);
    }
  } catch (error) {
    setError(error.message || 'Login failed');
  } finally {
    setLoading(false);
  }
};
```

#### C. SignupScreen Component
**Current:** Calls `onComplete()` directly
**Update:** Call API.Auth.signup()

```javascript
const handleSignup = async () => {
  try {
    setLoading(true);
    setError('');
    
    const response = await API.Auth.signup({
      business_name: businessName,
      contact_name: contactName,
      phone: phone,
      email: email,
      password: password,
      address: address
    });
    
    if (response.success) {
      onComplete(response.user);
    }
  } catch (error) {
    setError(error.message || 'Signup failed');
  } finally {
    setLoading(false);
  }
};
```

#### D. NewOrderScreen Component
**Current:** Creates order locally and adds to state
**Update:** Call appropriate API endpoint based on mode

```javascript
const handlePlaceOrder = async () => {
  try {
    setLoading(true);
    
    let response;
    
    if (mode === 'quick') {
      response = await API.Orders.createQuickSend({
        pickup_address: pickupAddress,
        sender_name: senderName,
        sender_phone: senderPhone,
        dropoff_address: dropoffAddress,
        receiver_name: receiverName,
        receiver_phone: receiverPhone,
        vehicle: vehicle,
        payment_method: payMethod,
        package_type: packageType,
        notes: notes
      });
    } else if (mode === 'multi') {
      response = await API.Orders.createMultiDrop({
        pickup_address: pickupAddress,
        sender_name: senderName,
        sender_phone: senderPhone,
        vehicle: vehicle,
        payment_method: payMethod,
        deliveries: drops.map(d => ({
          dropoff_address: d.address,
          receiver_name: d.name,
          receiver_phone: d.phone,
          package_type: d.pkg,
          notes: d.notes
        })),
        notes: notes
      });
    } else if (mode === 'bulk') {
      response = await API.Orders.createBulkImport({
        pickup_address: pickupAddress,
        sender_name: senderName,
        sender_phone: senderPhone,
        vehicle: vehicle,
        payment_method: payMethod,
        deliveries: bulkRows.map(r => ({
          dropoff_address: r.address,
          receiver_name: r.name,
          receiver_phone: r.phone,
          package_type: r.pkg,
          notes: r.notes || ''
        })),
        notes: notes
      });
    }
    
    if (response.success) {
      showNotif(response.message);
      // Reload orders
      const ordersResponse = await API.Orders.getOrders();
      if (ordersResponse.success) {
        setOrders(transformOrders(ordersResponse.orders));
      }
      // Navigate back to dashboard
      setScreen('dashboard');
    }
  } catch (error) {
    showNotif(error.message || 'Failed to create order', 'error');
  } finally {
    setLoading(false);
  }
};
```

#### E. OrdersScreen Component
**Current:** Filters local orders array
**Update:** Fetch from API with filters

```javascript
useEffect(() => {
  const loadOrders = async () => {
    try {
      const filters = {};
      if (tab === 'active') filters.status = 'Pending,Assigned,Started';
      if (tab === 'completed') filters.status = 'Done';
      if (tab === 'canceled') filters.status = 'CustomerCanceled,RiderCanceled';
      
      const response = await API.Orders.getOrders(filters);
      if (response.success) {
        setOrders(transformOrders(response.orders));
      }
    } catch (error) {
      console.error('Failed to load orders:', error);
    }
  };
  
  loadOrders();
}, [tab]);
```

---

## Data Transformation

The backend API returns data in a different format than the frontend expects. We need transformation functions:

### Transform Order Data

```javascript
function transformOrders(apiOrders) {
  return apiOrders.map(order => ({
    id: order.order_number,
    status: order.status,
    pickup: order.pickup_address,
    dropoff: order.deliveries[0]?.dropoff_address || '',
    amount: parseFloat(order.total_amount),
    date: formatDate(order.created_at),
    vehicle: order.vehicle_name,
    merchant: order.user_business_name,
    deliveries: order.deliveries,
    mode: order.mode,
    payment_method: order.payment_method
  }));
}

function formatDate(isoString) {
  const date = new Date(isoString);
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const month = months[date.getMonth()];
  const day = date.getDate();
  const hours = date.getHours();
  const minutes = date.getMinutes();
  const ampm = hours >= 12 ? 'PM' : 'AM';
  const displayHours = hours % 12 || 12;
  
  return `${month} ${day}, ${displayHours}:${minutes.toString().padStart(2, '0')} ${ampm}`;
}
```

---

## Implementation Steps

1. ✅ Create `api.js` with API service
2. ✅ Update `index.html` to include api.js
3. ⏳ Add data transformation functions to MerchantPortal.jsx
4. ⏳ Update LoginScreen to use API.Auth.login()
5. ⏳ Update SignupScreen to use API.Auth.signup()
6. ⏳ Update NewOrderScreen to use API.Orders methods
7. ⏳ Update OrdersScreen to fetch from API
8. ⏳ Update DashboardScreen to use API.Orders.getOrderStats()
9. ⏳ Add loading states and error handling
10. ⏳ Test all functionality

---

## Testing Checklist

- [ ] Login with existing account
- [ ] Signup new account
- [ ] View dashboard with real data
- [ ] Create Quick Send order
- [ ] Create Multi-Drop order
- [ ] Create Bulk Import order
- [ ] View orders list
- [ ] Filter orders by status
- [ ] View order details
- [ ] Logout

---

## Next Steps

Would you like me to:
1. **Automatically update MerchantPortal.jsx** with all API integrations?
2. **Create a step-by-step manual** for you to update it yourself?
3. **Create a new integrated version** as a separate file for testing?

