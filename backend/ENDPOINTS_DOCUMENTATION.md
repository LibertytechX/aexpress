# API Documentation

## Authentication Endpoints (Merchant Facing)
```
/api/auth/
```

### 1. Update/Get/Delete User Profile
**Endpoint:** `GET/PUT/DELETE /profile/`  
**Authentication:** Required (Bearer Token)  
**Description:** Get, update, or deactivate the current merchant's account.

**DELETE Behavior:**
- Soft-deactivates the account.
- **Pre-condition**: Must NOT have any active/ongoing orders.

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Your account has been deactivated successfully.",
  "data": {},
  "status_code": 200
}
```

---

## Dispatcher Portal API Documentation

## Base URL
```
/api/dispatcher/
```

## Merchant Management

### 1. List Merchants
**Endpoint:** `GET /merchants/`  
**Authentication:** Required (Dispatcher Admin)  
**Description:** Returns a list of all registered merchants.

---

### 2. Deactivate Merchant (Delete)
**Endpoint:** `DELETE /merchants/<merchant_id>/`  
**Authentication:** Required (Dispatcher Admin)  
**Description:** Soft-deactivates a merchant account. This sets `is_active=False` on the user and `activity_status='inactive'` on the merchant profile.

**Pre-conditions:**
- Merchant must NOT have any active/ongoing orders (Pending, Assigned, Started, etc.).

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Merchant [Business Name] deactivated successfully.",
  "data": {},
  "status_code": 200
}
```

**Error Response (400 Bad Request):**
```json
{
  "status": "error",
  "message": "Cannot delete merchant with active/ongoing orders.",
  "data": {},
  "status_code": 400
}
```

---

## Order Management

### 1. List Orders
**Endpoint:** `GET /orders/`  

---

## Rider Management

### 1. List Riders
**Endpoint:** `GET /riders/`

---

(More documentation to be added as needed)
