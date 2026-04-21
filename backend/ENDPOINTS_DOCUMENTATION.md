# API Documentation

---

## Rider Facing Endpoints
**Base URL:** `/api/riders/`

### 1. Today's Trips (Orders)
**Endpoint:** `GET /orders-today/`  
**Authentication:** Required (Rider Bearer Token)  
**Description:** Returns a list of completed orders for the authenticated rider. Supports period filtering.

**Query Parameters:**
- `period` (optional): Filter by date range. Options: `today` (default), `week` (last 7 days), `month` (last 30 days).

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "order_number": "AX-123456",
      "completed_at": "2026-04-17T09:00:00Z",
      "status": "Done",
      "total_amount": "1500.00",
      "deliveries": [...]
    }
  ]
}
```

---

### 2. Rider Earnings Stats
**Endpoint:** `GET /earnings/`  
**Authentication:** Required (Rider Bearer Token)  
**Description:** Returns aggregated earnings, trip counts, and COD collection stats for the authenticated rider.

**Query Parameters:**
- `period` (optional): Filter by date range. Options: `today` (default), `week` (last 7 days), `month` (last 30 days).

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "total_earnings": 5000.00,
    "trips_completed": 10,
    "cod_collected": 15000.00
  }
}
```

---

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
**Description:** Returns a paginated list of orders.
**Fields Added:**
- `vertical_lead_name`: The name of the lead responsible for the order's vertical.

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

---

## SmartParcel Locker Delivery Integration

> [!NOTE]
> All SmartParcel endpoints are proxied to the SmartParcel V2 Business sandbox API.
> In this version, all external requests use the `POST` method with the `apikey` sent in the request body.

## Base URL
```
/api/orders/smart-parcel/
```

**Authentication:** Required (Bearer Token or Merchant API Key)

---

### Geography

#### 1. List States
**Endpoint:** `GET /states/`  
**Description:** Returns all Nigerian states where SmartParcel currently operates.

**Success Response (200 OK):**
```json
{ "status": "success", "message": "SmartParcel states retrieved successfully.", "data": [...] }
```

---

#### 2. List Cities by State
**Endpoint:** `GET /states/<state_id>/cities/`  
**Description:** Returns cities within a specific state.

| Param | Type | Description |
|-------|------|-------------|
| `state_id` | path `str` | SmartParcel state identifier |

---

### Boxes

#### 3. List Boxes by City
**Endpoint:** `GET /boxes/city/<city_id>/`  
**Description:** Returns all boxes in a specific city.

| Param | Type | Description |
|-------|------|-------------|
| `city_id` | path `str` | SmartParcel city identifier |

---

#### 4. List Assigned Boxes by City
**Endpoint:** `GET /boxes/assigned/city/<city_id>/`  
**Description:** Returns all boxes assigned to the merchant in a specific city. Returns an empty list if no boxes are assigned.

| Param | Type | Description |
|-------|------|-------------|
| `city_id` | path `str` | SmartParcel city identifier |

---

#### 4. Get Box Details
**Endpoint:** `GET /boxes/<box_id>/`  
**Description:** Returns full details of a single SmartParcel locker box.

| Param | Type | Description |
|-------|------|-------------|
| `box_id` | path `str` | SmartParcel box identifier |

---

#### 5. List Available Boxes (Vacant Lockers)
**Endpoint:** `GET /boxes/available/?city_id=<city_id>`  
**Description:** Returns all boxes that currently have vacant lockers in a specific city.  

| Query Param | Type | Description |
|-------------|------|-------------|
| `city_id` | `str` | **Required**. Filter by city |

---

### Locker Sizes

#### 6. List Locker Sizes
**Endpoint:** `GET /locker-sizes/`  
**Description:** Returns all available locker size options on the SmartParcel network.

---

### Parcels

#### 7. Create Parcel
**Endpoint:** `POST /parcels/`  
**Description:** Creates a new parcel on the SmartParcel network.

**Request Body:**
```json
{
  "sender_name": "John Doe",
  "sender_phone": "08012345678",
  "sender_email": "john@example.com",
  "receiver_name": "Jane Doe",
  "receiver_phone": "08087654321",
  "receiver_email": "jane@example.com",
  "box_id": "BOX-001",
  "locker_size_id": "SIZE-S",
  "description": "Mobile phone",
  "value": 50000.00,
  "reference": "AX-ORDER-12345"
}
```

**Success Response (201 Created):**
```json
{
  "status": "success",
  "message": "SmartParcel parcel created successfully.",
  "data": { "tracking_number": "SP-XXXXXXXXXX", ... }
}
```

---

#### 8. Get Parcel Details
**Endpoint:** `GET /parcels/<tracking_number>/`  
**Description:** Returns details of a parcel by its tracking number.

---

---
 
 #### 9. Resolve Collect Code
 **Endpoint:** `GET /parcels/resolve-collect-code/<str:collect_code>/`  
 **Description:** Resolves a 4-8 character SmartParcel collect code to a pending parcel detail.
 
 | Param | Type | Description |
 |-------|------|-------------|
 | `collect_code` | path `str` | The SmartParcel collect code |
 
 ---
 
 #### 10. Cancel Parcel
**Endpoint:** `POST /parcels/<tracking_number>/cancel/`  
**Description:** Cancels an existing parcel on the SmartParcel network.

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "SmartParcel parcel cancelled successfully.",
  "data": {}
}
```

---

## Quick Send SmartParcel Integration
The `QuickSendView` supports automated SmartParcel locker workflows.

**Fields**:
- `is_pickup_percel` (bool): Pickup from locker.
- `isdelivery_percel` (bool): Deliver to locker.
- `collect_code` (str): Required for pickup.
- `box_id` (str): Required for delivery.
- `locker_size_id` (str): Required for delivery.

**Storage**: Full parcel JSON is stored in `order.percel_info`.
*(Note: Model fields currently retain the "percel" spelling to maintain database compatibility.)*

---

## Merchant Notifications
**Base URL:** `/api/auth/notifications/`

### 1. List Notifications
**Endpoint:** `GET /`  
**Description:** Returns all notifications for the authenticated merchant, newest first.

### 2. Mark as Read
**Endpoint:** `POST /<uuid:pk>/read/`  
**Description:** Marks a specific notification as read.

### 3. Mark All as Read
**Endpoint:** `POST /read-all/`  
**Description:** Marks all unread notifications as read.

### 4. Delete Notification
**Endpoint:** `DELETE /<uuid:pk>/`  
**Description:** Deletes a specific notification.

### 5. Clear All Notifications
**Endpoint:** `DELETE /delete-all/`  
**Description:** Deletes all notifications for the merchant.

### 6. Notification Settings
**Endpoint:** `GET/PATCH /settings/`  
**Description:** Retrieve or update notification toggle preferences (push_enabled, order_assigned, etc.).
