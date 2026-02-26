# Backend API Requirements - AX Rider App

## Overview

This document lists **ALL** backend API endpoints required for the AX Rider mobile app to function properly.

**Base URL**: `https://api.axpress.ng/api/v1/rider` (or your configured base URL)

**Start Super User**

Field	Value
Phone	08031346316
Password	Admin1234!
Email	inyang1@gmail.com
Is Superuser	✅

## End Super User

---

## 🔐 Authentication Endpoints

### 1. Login
- **Endpoint**: `POST /api/riders/auth/login/`
- **Purpose**: Authenticate rider with phone and password
- **Request Body**:
  ```json
  {
    "phone": "08012345678",
    "password": "password123",
    "device_id": "uuid-device-id",
    "device_name": "iPhone 15 Pro",
    "device_os": "ios",
    "fcm_token": "firebase-cloud-messaging-token"
  }
  ```
- **Response**:
  ```json
  {
    "tokens": {
      "access": "jwt-access-token",
      "refresh": "jwt-refresh-token"
    },
    "rider": {
      "id": "rider_001",
      "name": "John Doe",
      "phone": "08012345678",
      ...
    }
  }
  ```
- **Status**: ✅ **CRITICAL** - App cannot function without this

### 2. Biometric Login
- **Endpoint**: `POST /auth/biometric/`
- **Purpose**: Login using biometric authentication (fingerprint)
- **Request Body**:
  ```json
  {
    "device_id": "uuid-device-id",
    "biometric_token": "encrypted-biometric-token",
    "fcm_token": "firebase-token"
  }
  ```
- **Response**: Same as login
- **Status**: ⚠️ **OPTIONAL** - For biometric login feature

### 3. Register Biometric
- **Endpoint**: `POST /auth/biometric/register/`
- **Purpose**: Register device for biometric login
- **Request Body**:
  ```json
  {
    "device_id": "uuid-device-id",
    "device_name": "iPhone 15 Pro",
    "biometric_type": "fingerprint"
  }
  ```
- **Status**: ⚠️ **OPTIONAL** - For biometric login feature

### 4. Refresh Token
- **Endpoint**: `POST /auth/refresh/`
- **Purpose**: Refresh expired access token
- **Request Body**:
  ```json
  {
    "refresh": "jwt-refresh-token"
  }
  ```
- **Response**:
  ```json
  {
    "access": "new-jwt-access-token"
  }
  ```
- **Status**: ✅ **CRITICAL** - For maintaining user sessions

### 5. Logout
- **Endpoint**: `POST /auth/logout/`
- **Purpose**: Invalidate tokens and logout rider
- **Status**: ✅ **REQUIRED**

### 6. Change Password
- **Endpoint**: `POST /auth/change-password/`
- **Purpose**: Change rider's password
- **Request Body**:
  ```json
  {
    "old_password": "old123",
    "new_password": "new123"
  }
  ```
- **Status**: ✅ **REQUIRED**

### 7. Update FCM Token
- **Endpoint**: `POST /api/fcm-token/` (NEW - for Firebase)
- **Purpose**: Update rider's Firebase Cloud Messaging token
- **Request Body**:
  ```json
  {
    "fcm_token": "firebase-cloud-messaging-token"
  }
  ```
- **Status**: ✅ **CRITICAL** - For Firebase push notifications

---

## 👤 Profile Endpoints

### 8. Get Profile
- **Endpoint**: `GET /me/`
- **Purpose**: Get current rider's profile
- **Response**:
  ```json
  {
    "id": "rider_001",
    "name": "John Doe",
    "phone": "08012345678",
    "email": "john@example.com",
    "status": "active",
    "duty_status": "on_duty",
    "vehicle_type": "bike",
    "rating": 4.8,
    "total_deliveries": 150,
    ...
  }
  ```
- **Status**: ✅ **CRITICAL** - Displayed on home screen

### 9. Update Profile
- **Endpoint**: `PATCH /profile/`
- **Purpose**: Update rider profile information
- **Request Body**:
  ```json
  {
    "name": "John Doe",
    "email": "john@example.com",
    "address": "123 Main St"
  }
  ```
- **Status**: ✅ **REQUIRED**

### 10. Update Bank Details
- **Endpoint**: `PATCH /bank/`
- **Purpose**: Update bank account for withdrawals
- **Request Body**:
  ```json
  {
    "bank_name": "GTBank",
    "account_number": "0123456789",
    "account_name": "John Doe"
  }
  ```
- **Status**: ✅ **REQUIRED** - For wallet withdrawals

### 11. Upload Avatar
- **Endpoint**: `POST /avatar/`
- **Purpose**: Upload profile picture
- **Request**: Multipart form data with image file
- **Status**: ⚠️ **OPTIONAL**

---

## 🚴 Duty Status Endpoints

### 12. Toggle Duty Status
- **Endpoint**: `POST /duty/`
- **Purpose**: Toggle rider between on-duty and off-duty
- **Request Body**:
  ```json
  {
    "status": "on_duty",  // or "off_duty"
    "latitude": 6.5244,
    "longitude": 3.3792
  }
  ```
- **Response**:
  ```json
  {
    "status": "on_duty",
    "timestamp": "2024-01-15T10:30:00Z"
  }
  ```
- **Status**: ✅ **CRITICAL** - Core functionality

---

## 📦 Order Endpoints

### 13. Get Assigned Orders
- **Endpoint**: `GET /orders/assigned/`
- **Purpose**: Get list of orders assigned to rider
- **Response**: Array of order objects
- **Status**: ✅ **CRITICAL** - Main screen content

### 14. Get Order Detail
- **Endpoint**: `GET /orders/{order_id}/`
- **Purpose**: Get detailed information about specific order
- **Status**: ✅ **CRITICAL**

### 15. Start Order
- **Endpoint**: `POST /orders/{order_id}/start/`
- **Purpose**: Mark order as started (heading to pickup)
- **Request Body**:
  ```json
  {
    "latitude": 6.5244,
    "longitude": 3.3792
  }
  ```
- **Status**: ✅ **CRITICAL**

### 16. Arrived at Pickup
- **Endpoint**: `POST /orders/{order_id}/arrived/`
- **Purpose**: Mark arrival at pickup location
- **Status**: ✅ **CRITICAL**

### 17. Pickup Order
- **Endpoint**: `POST /orders/{order_id}/pickup/`
- **Purpose**: Mark order as picked up
- **Request Body**:
  ```json
  {
    "latitude": 6.5244,
    "longitude": 3.3792,
    "pickup_time": "2024-01-15T10:30:00Z"
  }
  ```
- **Status**: ✅ **CRITICAL**

### 18. Arrived at Dropoff
- **Endpoint**: `POST /orders/{order_id}/at-dropoff/`
- **Purpose**: Mark arrival at dropoff location
- **Status**: ✅ **CRITICAL**

### 19. Deliver Order
- **Endpoint**: `POST /orders/{order_id}/deliver/`
- **Purpose**: Mark order as delivered
- **Status**: ✅ **CRITICAL**

### 20. Complete Order
- **Endpoint**: `POST /orders/{order_id}/complete/`
- **Purpose**: Complete order and finalize
- **Request Body**:
  ```json
  {
    "latitude": 6.5244,
    "longitude": 3.3792,
    "completion_time": "2024-01-15T11:00:00Z",
    "notes": "Delivered successfully"
  }
  ```
- **Status**: ✅ **CRITICAL**

### 21. Cancel Order
- **Endpoint**: `POST /orders/{order_id}/cancel/`
- **Purpose**: Cancel order with reason
- **Request Body**:
  ```json
  {
    "reason": "Customer not available",
    "notes": "Called multiple times"
  }
  ```
- **Status**: ✅ **REQUIRED**

### 22. Record COD Payment
- **Endpoint**: `POST /orders/{order_id}/cod/`
- **Purpose**: Record cash-on-delivery payment
- **Request Body**:
  ```json
  {
    "amount": 5000,
    "payment_method": "cash"
  }
  ```
- **Status**: ✅ **CRITICAL** - For COD orders

### 23. Upload Proof of Delivery
- **Endpoint**: `POST /orders/{order_id}/proof/`
- **Purpose**: Upload delivery proof (photo, barcode, signature)
- **Request**: Multipart form data
  ```
  phase: "pickup" or "delivery"
  proof_type: "photo", "barcode", "signature"
  file: image file
  barcode_value: "scanned-barcode-value"
  notes: "Additional notes"
  latitude: 6.5244
  longitude: 3.3792
  ```
- **Status**: ✅ **CRITICAL** - Required for order completion

### 24. Get Order History
- **Endpoint**: `GET /orders/history/`
- **Purpose**: Get rider's completed orders
- **Query Parameters**: `?page=1&limit=20&status=completed`
- **Status**: ✅ **REQUIRED**

---

## 🎯 Offer Endpoints (For You Tab)

### 25. Get Available Offers
- **Endpoint**: `GET /offers/`
- **Purpose**: Get list of available order offers
- **Response**: Array of offer objects
- **Status**: ✅ **CRITICAL** - "For You" tab content

### 26. Accept Offer
- **Endpoint**: `POST /offers/{offer_id}/accept/`
- **Purpose**: Accept an order offer
- **Response**: Full order object
- **Status**: ✅ **CRITICAL**

### 27. Decline Offer
- **Endpoint**: `POST /offers/{offer_id}/decline/`
- **Purpose**: Decline an order offer
- **Request Body**:
  ```json
  {
    "reason": "Too far", "Too busy", etc.
  }
  ```
- **Status**: ✅ **CRITICAL**

---

## 🛣️ Route Endpoints

### 28. Get Routes
- **Endpoint**: `GET /routes/`
- **Purpose**: Get delivery routes assigned to rider
- **Query Parameters**: `?status=active` or `?status=completed`
- **Response**: Array of route objects with multiple stops
- **Status**: ✅ **CRITICAL** - Routes screen content

### 29. Get Route Detail
- **Endpoint**: `GET /routes/{route_id}/`
- **Purpose**: Get detailed route information with all stops
- **Status**: ✅ **CRITICAL**

### 30. Start Route Stop
- **Endpoint**: `POST /routes/{route_id}/stops/{stop_id}/start/`
- **Purpose**: Mark a route stop as started
- **Status**: ✅ **CRITICAL**

### 31. Complete Route Stop
- **Endpoint**: `POST /routes/{route_id}/stops/{stop_id}/complete/`
- **Purpose**: Mark a route stop as completed
- **Status**: ✅ **CRITICAL**

---

## 💰 Earnings Endpoints

### 32. Get Earnings Summary
- **Endpoint**: `GET /earnings/`
- **Purpose**: Get earnings summary for different periods
- **Query Parameters**: `?period=today` or `?period=week` or `?period=month`
- **Response**:
  ```json
  {
    "period": "today",
    "total_earnings": 15000,
    "total_deliveries": 12,
    "total_distance": 45.5,
    "total_hours": 6.5,
    "breakdown": {
      "base_fare": 10000,
      "distance_bonus": 3000,
      "tips": 2000
    }
  }
  ```
- **Status**: ✅ **CRITICAL** - Earnings screen content

---

## 💳 Wallet Endpoints

### 33. Get Wallet Balance
- **Endpoint**: `GET /wallet/`
- **Purpose**: Get current wallet balance
- **Response**:
  ```json
  {
    "balance": 45000,
    "pending": 5000,
    "available": 40000,
    "currency": "NGN"
  }
  ```
- **Status**: ✅ **CRITICAL** - Wallet screen content

### 34. Get Wallet Transactions
- **Endpoint**: `GET /wallet/transactions/`
- **Purpose**: Get wallet transaction history
- **Query Parameters**: `?page=1&limit=20`
- **Response**: Array of transaction objects
- **Status**: ✅ **CRITICAL**

### 35. Withdraw Funds
- **Endpoint**: `POST /wallet/withdraw/`
- **Purpose**: Request withdrawal to bank account
- **Request Body**:
  ```json
  {
    "amount": 10000
  }
  ```
- **Status**: ✅ **CRITICAL** - Withdrawal feature

---

## 📍 Location Endpoints

### 36. Update Location
- **Endpoint**: `POST /location/`
- **Purpose**: Update rider's current location (real-time tracking)
- **Request Body**:
  ```json
  {
    "latitude": 6.5244,
    "longitude": 3.3792,
    "speed_kmh": 25.5,
    "battery_pct": 85
  }
  ```
- **Status**: ✅ **CRITICAL** - Real-time tracking
- **Note**: Called every 30 seconds when on duty

### 37. Batch Location Update
- **Endpoint**: `POST /location/batch/`
- **Purpose**: Upload multiple location points at once
- **Request Body**:
  ```json
  {
    "locations": [
      {
        "latitude": 6.5244,
        "longitude": 3.3792,
        "timestamp": "2024-01-15T10:30:00Z",
        "speed_kmh": 25.5
      }
    ]
  }
  ```
- **Status**: ⚠️ **OPTIONAL** - For offline location buffering

---

## 🔔 Notification Endpoints

### 38. Get Notifications
- **Endpoint**: `GET /notifications/`
- **Purpose**: Get rider's notifications
- **Response**: Array of notification objects
- **Status**: ✅ **REQUIRED** - Notifications screen

### 39. Mark Notification as Read
- **Endpoint**: `PATCH /notifications/{notification_id}/read/`
- **Purpose**: Mark single notification as read
- **Status**: ✅ **REQUIRED**

### 40. Mark All Notifications as Read
- **Endpoint**: `POST /notifications/read-all/`
- **Purpose**: Mark all notifications as read
- **Status**: ✅ **REQUIRED**

---

## 📄 Document Endpoints

### 41. Get Documents
- **Endpoint**: `GET /documents/`
- **Purpose**: Get rider's uploaded documents (license, insurance, etc.)
- **Response**: Array of document objects
- **Status**: ⚠️ **OPTIONAL** - Document management

### 42. Upload Document
- **Endpoint**: `POST /documents/upload/`
- **Purpose**: Upload rider documents
- **Request**: Multipart form data
  ```
  doc_type: "license", "insurance", "vehicle_registration"
  file: document file
  expires_at: "2025-12-31"
  ```
- **Status**: ⚠️ **OPTIONAL**

---

## 🆘 Support Endpoints

### 43. Create Support Ticket
- **Endpoint**: `POST /support/`
- **Purpose**: Create support ticket
- **Request Body**:
  ```json
  {
    "category": "technical",
    "subject": "Payment not received",
    "message": "I completed order AX-12345 but haven't received payment",
    "order_id": "order_123"
  }
  ```
- **Status**: ✅ **REQUIRED** - Support/help feature

### 44. Get Support Tickets
- **Endpoint**: `GET /support/tickets/`
- **Purpose**: Get rider's support tickets
- **Status**: ⚠️ **OPTIONAL**

---

## 📊 Area Demand Endpoints

### 45. Get Area Demand
- **Endpoint**: `GET /demand/`
- **Purpose**: Get high-demand areas (heat map)
- **Response**:
  ```json
  [
    {
      "area": "Ikeja",
      "latitude": 6.5244,
      "longitude": 3.3792,
      "demand_level": "high",
      "active_orders": 15,
      "surge_multiplier": 1.5
    }
  ]
  ```
- **Status**: ⚠️ **OPTIONAL** - Heat map feature

---

## 🔥 Firebase Cloud Messaging (NEW)

### 46. Send Push Notification (Backend → App)
- **Method**: Firebase Admin SDK
- **Purpose**: Send real-time notifications to riders
- **Status**: ✅ **CRITICAL** - Real-time notifications
- **Note**: Replaces WebSocket/Ably for push notifications

**Message Types:**

#### Incoming Order:
```python
from firebase_admin import messaging
import json

message = messaging.Message(
    data={
        'type': 'incoming_order',
        'offer': json.dumps({
            'id': 'offer_123',
            'orderId': 'order_456',
            'estimatedEarnings': '2500',
            'distanceKm': '5.2',
            'etaMins': '15',
            'pickupAddress': '123 Main St',
            'dropoffAddress': '456 Oak Ave',
            'merchantName': 'Shoprite',
            'vehicleType': 'bike',
            'paymentMethod': 'cash',
            'codAmount': '0',
            'secondsRemaining': '300',
            'expiresAt': '2024-01-15T10:30:00Z',
        })
    },
    token=rider.fcm_token,
    notification=messaging.Notification(
        title='🚴 New Order Incoming!',
        body='₦2500 · 5.2km',
    ),
    android=messaging.AndroidConfig(
        priority='high',
    ),
    apns=messaging.APNSConfig(
        payload=messaging.APNSPayload(
            aps=messaging.Aps(
                sound='default',
            ),
        ),
    ),
)
messaging.send(message)
```

#### Order Update:
```python
message = messaging.Message(
    data={
        'type': 'order_update',
        'order_id': 'order_456',
        'status': 'picked_up',
        'timestamp': '2024-01-15T10:35:00Z',
    },
    token=rider.fcm_token,
    notification=messaging.Notification(
        title='Order Update',
        body='Order picked up successfully',
    ),
)
messaging.send(message)
```

#### General Notification:
```python
message = messaging.Message(
    data={
        'type': 'notification',
        'title': 'New Bonus Available',
        'body': 'Complete 5 more deliveries today!',
        'priority': 'high',
    },
    token=rider.fcm_token,
    notification=messaging.Notification(
        title='New Bonus Available',
        body='Complete 5 more deliveries today!',
    ),
)
messaging.send(message)
```

---

## 📋 Summary by Priority

### ✅ CRITICAL (App Cannot Function Without These)
1. **Login** - `POST /api/riders/auth/login/`
2. **Refresh Token** - `POST /auth/refresh/`
3. **Update FCM Token** - `POST /api/fcm-token/` (NEW)
4. **Get Profile** - `GET /me/`
5. **Toggle Duty Status** - `POST /duty/`
6. **Get Assigned Orders** - `GET /orders/assigned/`
7. **Get Order Detail** - `GET /orders/{order_id}/`
8. **Order Lifecycle** - Start/Pickup/Deliver/Complete
9. **Upload Proof of Delivery** - `POST /orders/{order_id}/proof/`
10. **Get Available Offers** - `GET /offers/`
11. **Accept/Decline Offer** - `POST /offers/{offer_id}/accept|decline/`
12. **Get Routes** - `GET /routes/`
13. **Route Stop Start/Complete** - `POST /routes/{route_id}/stops/{stop_id}/start|complete/`
14. **Get Earnings Summary** - `GET /earnings/`
15. **Get Wallet Balance** - `GET /wallet/`
16. **Get Wallet Transactions** - `GET /wallet/transactions/`
17. **Update Location** - `POST /location/`
18. **Firebase Push Notifications** - Backend sends via Firebase Admin SDK

### ✅ REQUIRED (Important Features)
19. **Logout** - `POST /auth/logout/`
20. **Change Password** - `POST /auth/change-password/`
21. **Update Profile** - `PATCH /profile/`
22. **Update Bank Details** - `PATCH /bank/`
23. **Record COD Payment** - `POST /orders/{order_id}/cod/`
24. **Cancel Order** - `POST /orders/{order_id}/cancel/`
25. **Get Order History** - `GET /orders/history/`
26. **Withdraw Funds** - `POST /wallet/withdraw/`
27. **Get Notifications** - `GET /notifications/`
28. **Mark Notifications as Read** - `PATCH /notifications/{id}/read/`
29. **Create Support Ticket** - `POST /support/`

### ⚠️ OPTIONAL (Nice to Have)
30. **Biometric Login** - `POST /auth/biometric/`
31. **Register Biometric** - `POST /auth/biometric/register/`
32. **Upload Avatar** - `POST /avatar/`
33. **Batch Location Update** - `POST /location/batch/`
34. **Get/Upload Documents** - `GET|POST /documents/`
35. **Get Support Tickets** - `GET /support/tickets/`
36. **Get Area Demand** - `GET /demand/`

---

## 🔧 Backend Setup Requirements

### 1. Install Firebase Admin SDK
```bash
pip install firebase-admin
```

### 2. Initialize Firebase in Django
```python
# settings.py or firebase_config.py
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred)
```

### 3. Database Schema Updates
Add to Rider model:
```python
class Rider(models.Model):
    # ... existing fields
    fcm_token = models.CharField(max_length=255, blank=True, null=True)
    fcm_token_updated_at = models.DateTimeField(auto_now=True)
    device_id = models.CharField(max_length=255, blank=True, null=True)
    device_name = models.CharField(max_length=100, blank=True, null=True)
    device_os = models.CharField(max_length=20, blank=True, null=True)
```

### 4. Authentication
- All endpoints (except login) require JWT authentication
- Include in headers: `Authorization: Bearer <access_token>`
- Token expires after 24 hours (configurable)
- Use refresh token to get new access token

### 5. Response Format
All successful responses should follow this format:
```json
{
  "success": true,
  "data": { ... },
  "message": "Success message"
}
```

Error responses:
```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

### 6. Common HTTP Status Codes
- `200 OK` - Successful GET/PATCH
- `201 Created` - Successful POST (resource created)
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Valid token but insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## 📞 Testing & Documentation

### Testing Endpoints
Use tools like:
- **Postman** - API testing
- **cURL** - Command line testing
- **Django REST Framework Browsable API** - Built-in testing

### Example cURL Request
```bash
# Login
curl -X POST https://api.axpress.ng/api/riders/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "08012345678",
    "password": "password123",
    "device_id": "test-device",
    "fcm_token": "test-fcm-token"
  }'

# Get Profile (with auth)
curl -X GET https://api.axpress.ng/api/v1/rider/me/ \
  -H "Authorization: Bearer <access_token>"
```

### Firebase Testing
Use Firebase Console to send test messages:
1. Go to Firebase Console → Cloud Messaging
2. Send test message to specific FCM token
3. Verify app receives the message

---

## 📚 Additional Resources

For more details, refer to:
- **`FIREBASE_SETUP.md`** - Complete Firebase integration guide
- **`FIREBASE_QUICK_REFERENCE.md`** - Quick reference for Firebase
- **`lib/services/api_service.dart`** - API service implementation
- **`lib/config/api.dart`** - Endpoint definitions
- **`lib/models/models.dart`** - Data models

---

## 🎯 Implementation Priority

### Phase 1: Core Functionality (Week 1)
- [ ] Authentication (Login, Refresh Token, Logout)
- [ ] Profile (Get Profile, Update Profile)
- [ ] Duty Status (Toggle Duty)
- [ ] Orders (Get Assigned, Order Detail, Order Lifecycle)
- [ ] Location (Update Location)
- [ ] Firebase FCM Token endpoint

### Phase 2: Order Management (Week 2)
- [ ] Offers (Get, Accept, Decline)
- [ ] Proof of Delivery (Upload)
- [ ] COD Payment Recording
- [ ] Order History

### Phase 3: Financial (Week 3)
- [ ] Earnings (Get Summary)
- [ ] Wallet (Balance, Transactions, Withdraw)
- [ ] Bank Details (Update)

### Phase 4: Additional Features (Week 4)
- [ ] Routes (Get, Detail, Stop Management)
- [ ] Notifications (Get, Mark Read)
- [ ] Support (Create Ticket)
- [ ] Firebase Push Notifications (Backend implementation)

### Phase 5: Optional Features (Future)
- [ ] Biometric Authentication
- [ ] Documents Management
- [ ] Area Demand/Heat Map
- [ ] Batch Location Updates

---

**Document Version**: 1.0
**Last Updated**: 2024-01-15
**Contact**: Backend Team

