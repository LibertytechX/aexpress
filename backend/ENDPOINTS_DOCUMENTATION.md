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

## Chat System API Documentation

> [!TIP]
> **Real-time Integration:** For real-time chat updates using Ably, see the detailed [Ably Realtime Chats Integration Guide](file:///Users/mac/Liberty/aexpress/backend/ably_realtime_chats.md).

## Base URL
```
/api/chats/
```

### 1. List Conversations
**Endpoint:** `GET /conversations/`  
**Authentication:** Required (Dispatcher/Agent)  
**Description:** Returns a list of all conversations ordered by most recent activity.
**Query Parameters:**
- `type` (optional): Filter by user type (`customer` or `rider`).
- `active` (optional): Filter by active status (`true` or `false`).

---

### 2. Start/Get Conversation
**Endpoint:** `POST /conversations/start/`  
**Authentication:** Required (Customer/Rider/Merchant)  
**Description:** Opens a support conversation or returns the existing active one for the authenticated user.

---

### 3. List Messages
**Endpoint:** `GET /conversations/<uuid:pk>/messages/`  
**Authentication:** Required  
**Description:** Returns the paginated message history for a specific conversation.

---

### 4. Send Message
**Endpoint:** `POST /conversations/<uuid:pk>/messages/send/`  
**Authentication:** Required  
**Description:** Sends a message in a conversation. 
**Request Body:**
```json
{
  "content": "Hello, I need help with my order."
}
```

---

### 5. Mark as Read
**Endpoint:** `POST /conversations/<uuid:pk>/read/`  
**Authentication:** Required (Agent)  
**Description:** Marks all unread messages in the conversation as read and resets the unread count.
