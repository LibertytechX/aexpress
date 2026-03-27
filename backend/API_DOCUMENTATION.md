# AX Merchant Portal - Authentication API Documentation

## Base URL
```
http://127.0.0.1:8000/api/auth
```

## Authentication Endpoints

### 1. User Signup
**Endpoint:** `POST /api/auth/signup/`  
**Authentication:** Not required  
**Description:** Register a new merchant account

**Request Body:**
```json
{
  "business_name": "Test Logistics Ltd",
  "contact_name": "John Doe",
  "phone": "08012345678",
  "email": "test@testlogistics.com",
  "address": "123 Test Street, Lagos",
  "password": "securepass123",
  "confirm_password": "securepass123",
  "referral_code": "LP-12345"
}
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "message": "Account created successfully!",
  "user": {
    "id": "uuid-here",
    "business_name": "Test Logistics Ltd",
    "contact_name": "John Doe",
    "phone": "08012345678",
    "email": "test@testlogistics.com",
    "address": "123 Test Street, Lagos",
    "is_active": true,
    "email_verified": false,
    "phone_verified": false,
    "created_at": "2026-02-14T21:49:00.715431Z",
    "updated_at": "2026-02-14T21:49:00.794690Z",
    "last_login": null
  },
  "tokens": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "errors": {
    "phone": ["This phone number is already registered."],
    "email": ["This email is already registered."],
    "confirm_password": ["Passwords do not match."]
  }
}
```

---

### 2. User Login
**Endpoint:** `POST /api/auth/login/`  
**Authentication:** Not required  
**Description:** Login with phone and password

**Request Body:**
```json
{
  "phone": "08012345678",
  "password": "securepass123"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Login successful!",
  "user": {
    "id": "uuid-here",
    "business_name": "Test Logistics Ltd",
    "contact_name": "John Doe",
    "phone": "08012345678",
    "email": "test@testlogistics.com",
    "address": "123 Test Street, Lagos",
    "is_active": true,
    "email_verified": false,
    "phone_verified": false,
    "created_at": "2026-02-14T21:49:00.715431Z",
    "updated_at": "2026-02-14T21:49:00.840013Z",
    "last_login": "2026-02-14T21:49:00.963739Z"
  },
  "tokens": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "errors": {
    "non_field_errors": ["Invalid phone number or password."]
  }
}
```

---

### 3. Get User Profile
**Endpoint:** `GET /api/auth/me/`  
**Authentication:** Required (Bearer Token)  
**Description:** Get current user profile

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "user": {
    "id": "uuid-here",
    "business_name": "Test Logistics Ltd",
    "contact_name": "John Doe",
    "phone": "08012345678",
    "email": "test@testlogistics.com",
    "address": "123 Test Street, Lagos",
    "is_active": true,
    "email_verified": false,
    "phone_verified": false,
    "created_at": "2026-02-14T21:49:00.715431Z",
    "updated_at": "2026-02-14T21:49:00.794690Z",
    "last_login": "2026-02-14T21:49:00.963739Z"
  }
}
```

---

### 4. Update User Profile
**Endpoint:** `PUT /api/auth/profile/`  
**Authentication:** Required (Bearer Token)  
**Description:** Update current user profile

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (all fields optional):**
```json
{
  "business_name": "Updated Logistics Ltd",
  "contact_name": "Jane Doe",
  "email": "newemail@testlogistics.com",
  "address": "456 New Street, Lagos"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Profile updated successfully!",
  "user": { ... }
}
```

---

### 5. Refresh Access Token
**Endpoint:** `POST /api/auth/refresh/`  
**Authentication:** Not required  
**Description:** Get a new access token using refresh token

**Request Body:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### 6. Logout
**Endpoint:** `POST /api/auth/logout/`  
**Authentication:** Required (Bearer Token)  
**Description:** Logout user by blacklisting refresh token

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Logout successful!"
}
```

---

## Token Lifetimes
- **Access Token:** 24 hours
- **Refresh Token:** 168 hours (7 days)

## Error Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid/expired token)
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error


---

## Postpaid Payment Plan Endpoints

### 1. List Postpaid Plans
**Endpoint:** `GET /api/subscriptions/postpaid/plans/`  
**Authentication:** Required (Bearer Token)  
**Description:** List all available postpaid plans (Weekly/Monthly)

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Postpaid plans retrieved successfully.",
  "data": [
    {
      "id": "uuid-here",
      "name": "Weekly Postpaid",
      "plan_type": "weekly",
      "is_active": true
    }
  ]
}
```

---

### 2. Activate Postpaid Plan
**Endpoint:** `POST /api/subscriptions/postpaid/plans/<plan_id>/activate/`  
**Authentication:** Required (Merchant only)  
**Description:** Activate a postpaid plan for the merchant

**Success Response (201 Created):**
```json
{
  "status": "success",
  "message": "Successfully activated Weekly Postpaid plan.",
  "data": {
    "id": "uuid-here",
    "status": "active",
    "accumulated_amount": "0.00",
    "current_period_start": "2026-03-27T15:18:51Z",
    "current_period_end": "2026-04-03T15:18:51Z",
    "plan": { ... }
  }
}
```

---

### 3. Get Active Postpaid Subscription
**Endpoint:** `GET /api/subscriptions/postpaid/active/`  
**Authentication:** Required (Bearer Token)  
**Description:** Get the merchant's current active or blocked postpaid subscription and accumulation status

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Postpaid subscription retrieved successfully.",
  "data": {
    "id": "uuid-here",
    "status": "active", // active, blocked, inactive
    "accumulated_amount": "1500.00",
    "current_period_end": "2026-04-03T15:18:51Z",
    "invoices": [ ... ]
  }
}
```

---

### 4. Get Postpaid Invoice Detail
**Endpoint:** `GET /api/subscriptions/postpaid/invoices/<invoice_id>/`  
**Authentication:** Required (Bearer Token)  
**Description:** Get details and payment info (virtual account) for a postpaid invoice

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Postpaid invoice retrieved successfully.",
  "data": {
    "id": "uuid-here",
    "amount": "5000.00",
    "status": "pending", // pending, paid, failed
    "payment_ref": "POST-INV-...",
    "payment_info": {
      "account_number": "1234567890",
      "bank_name": "Test Bank",
      "account_name": "Liberty AXpress"
    },
    "due_date": "2026-03-28T15:18:51Z"
  }
}
```

---

## Order Integration
Merchants with an active, non-blocked postpaid plan can now select `"postpaid"` as a `payment_method` when creating orders via `QuickSend`, `MultiDrop`, or `BulkImport`. The order amount will be added to their `accumulated_amount`, and the order `payment_status` will be set to `"Postpaid"`.

