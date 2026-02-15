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
  "confirm_password": "securepass123"
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

