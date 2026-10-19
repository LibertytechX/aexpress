# API Documentation

---

## Rider Facing Endpoints
**Base URL:** `/api/riders/`

### 0. Rider Self-Registration
**Endpoint:** `POST /auth/register/`  
**Authentication:** None (Public)  
**Description:** Registers a new independent/freelancer rider account with personal details, emergency contact information, BVN, vehicle specifications, and required KYC documents. Generates JWT tokens and session immediately with account pending ops review (`is_authorized=False`).

**Request Body:**
```json
{
  "phone": "08012345678",
  "email": "rider@example.com",
  "first_name": "Ade",
  "last_name": "Babatunde",
  "password": "Password123!",
  "confirm_password": "Password123!",
  "address": "123 Lagos St, Ikeja",
  "emergency_contact_name": "Bola Babatunde",
  "emergency_phone": "08098765432",
  "bvn": "12345678901",
  "vehicle_model": "Honda Ace 125",
  "vehicle_plate_number": "LAG-123-XY",
  "vehicle_color": "Red",
  "vehicle_photo": "https://storage.aexpress.com/vehicles/photo.jpg",
  "device_id": "device-uuid-123",
  "device_name": "Samsung Galaxy",
  "device_os": "android",
  "fcm_token": "fcm-token-123",
  "rider_documents": [
    {
      "type": "national_id",
      "url": "https://storage.aexpress.com/docs/nin.pdf"
    },
    {
      "type": "riders_card",
      "url": "https://storage.aexpress.com/docs/rcard.pdf"
    },
    {
      "type": "drivers_license",
      "url": "https://storage.aexpress.com/docs/license.pdf"
    },
    {
      "type": "utility_bill",
      "url": "https://storage.aexpress.com/docs/bill.pdf"
    },
    {
      "type": "profile_photo",
      "url": "https://storage.aexpress.com/docs/photo.jpg"
    }
  ]
}
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "message": "Registration successful! Your account is pending review.",
  "tokens": {
    "access": "eyJ0eXAi...",
    "refresh": "eyJ0eXAi..."
  },
  "rider": {
    "id": "uuid",
    "rider_id": "R12345",
    "status": "offline",
    "firstName": "Ade",
    "lastName": "Babatunde",
    "phone": "+2348012345678",
    "email": "rider@example.com",
    "emergency_contact_name": "Bola Babatunde",
    "emergency_phone": "+2348098765432",
    "vehicle_model": "Honda Ace 125",
    "vehicle_plate_number": "LAG-123-XY",
    "rating": "0.00",
    "total_deliveries": 0,
    "wallet_balance": 0.0,
    "pending_cod": 0.0,
    "acceptance_rate": 100.0,
    "on_time_rate": 100.0,
    "documents_status": {
      "total": 5,
      "approved": 0,
      "pending": 5,
      "expiring_soon": 0
    },
    "net_earnings": 0.0
  }
}
```

---

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

### 3. Rider Wallet Transactions
**Endpoint:** `GET /wallet/transactions/`  
**Authentication:** Required (Rider Bearer Token)  
**Description:** Returns a paginated list of wallet transaction history for the authenticated rider.

**Query Parameters:**
- `page` (optional): Page number.
- `page_size` (optional): Results per page (default: 20, max: 100).

**Success Response (200 OK):**
```json
{
  "success": true,
  "count": 2,
  "next": null,
  "previous": null,
  "data": [
    {
      "id": "uuid",
      "type": "debit",
      "amount": "500.00",
      "description": "Test Debit",
      "reference": "TXN-XXXXXX",
      "balance_before": "1000.00",
      "balance_after": "500.00",
      "status": "completed",
      "created_at": "2026-05-19T14:00:00Z"
    },
    {
      "id": "uuid",
      "type": "credit",
      "amount": "1000.00",
      "description": "Test Credit",
      "reference": "TXN-YYYYYY",
      "balance_before": "0.00",
      "balance_after": "1000.00",
      "status": "completed",
      "created_at": "2026-05-19T13:00:00Z"
    }
  ]
}
---

### 3a. Supported Banks Directory
**Endpoint:** `GET /banks/`  
**Authentication:** None (Public / Open)  
**Description:** Retrieves the complete directory of supported Nigerian commercial banks, microfinance banks, and fintech institutions with their corresponding 3-digit and 6-digit CBN/NIBSS codes and USSD shortcodes. Cached in Redis for ultra-low latency.

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Banks retrieved successfully.",
  "data": [
    {
      "id": 1,
      "name": "Access Bank",
      "bank_code": "044",
      "cbn_code": "000014",
      "ussd_short_code": "*901#",
      "bank_short_name": "ACCESS"
    },
    {
      "id": 6,
      "name": "Wema Bank",
      "bank_code": "035",
      "cbn_code": "000017",
      "ussd_short_code": "*945#",
      "bank_short_name": "WEMA"
    }
  ]
}
```

---

### 3b. Verify Bank Account Number
**Endpoint:** `POST /wallet/verify-account/`  
**Authentication:** None (Public / AllowAny)  
**Description:** Validates a 10-digit NUBAN account number and resolves the account name using the LibertyPay Account Enquiry integration.

**Request Body:**
```json
{
  "account_number": "0123456789",
  "bank_code": "044"
}
```

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Account verified successfully.",
  "data": {
    "account_number": "0123456789",
    "account_name": "ADE BABATUNDE",
    "bank_code": "044",
    "cbn_code": "000014",
    "currency_code": "NGN"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "status": "error",
  "message": "Account verification failed. Please check the account number and bank code.",
  "data": null
}
```

---

### 3c. Withdraw Earnings (Independent Riders)
**Endpoint:** `POST /wallet/withdraw/`  
**Authentication:** Required (Rider Bearer Token)  
**Description:** Allows independent riders (`is_independent_rider=True`) to withdraw delivery earnings from their wallet to their external bank account via Wema CoreBanking payout.
1. Checks whether the platform **Independent Rider Payout Wallet Pool** has sufficient funds to disburse the withdrawal.
2. Validates that the withdrawal amount does not exceed the rider's `withdrawable_balance` (wallet balance minus any unremitted Cash on Delivery).
3. Atomically debits both the **Independent Rider Payout Wallet Pool** (creating an immutable debit ledger entry) and the rider's personal wallet.
4. Triggers the external Wema CoreBanking payout. If rejected or failed, automatically issues an immediate automated refund to **both** the rider's wallet and the payout pool.

**Request Body:**
```json
{
  "amount": "5000.00",
  "account_number": "0123456789",
  "account_name": "ADE BABATUNDE",
  "bank_code": "044",
  "bank_name": "Access Bank",
  "narration": "Payout for deliveries",
  "is_sandbox": false
}
```
> **Sandbox Testing:** Pass `"is_sandbox": true` or `"mode": "SANDBOX"` in the request body (or add `?sandbox=true` query parameter) to trigger sandbox withdrawal. In sandbox mode, reference IDs use the `WDR-SBX-` prefix, CoreBanking payouts are simulated/tested without moving live funds, and test pool liquidity is automatically provisioned if the development payout pool has insufficient funds.

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Withdrawal request processed successfully.",
  "data": {
    "reference": "WDR-A1B2C3D4E5F6",
    "amount": 5000.0,
    "account_number": "0123456789",
    "account_name": "ADE BABATUNDE",
    "bank_code": "044",
    "status": "success",
    "remaining_balance": 15000.0,
    "is_sandbox": false,
    "mode": "LIVE"
  }
}
```

**Error Responses:**
- **400 Bad Request (Insufficient Payout Pool Balance):**
```json
{
  "status": "error",
  "message": "Insufficient funds in payout pool. Unable to process withdrawal at this time.",
  "data": null
}
```
- **400 Bad Request (Insufficient Withdrawable Balance or Unremitted COD):**
```json
{
  "status": "error",
  "message": "Insufficient withdrawable balance. Withdrawable: ₦2,000.00 (Pending unremitted COD: ₦8,000.00)",
  "data": null
}
```
- **403 Forbidden (Non-Independent Rider):**
```json
{
  "status": "error",
  "message": "Only independent riders are permitted to withdraw wallet earnings.",
  "data": null
}
```
- **422 Unprocessable Entity (Transfer Rejected, Wallet & Pool Refunded):**
```json
{
  "status": "error",
  "message": "Destination bank connection timeout. Your wallet balance has been refunded.",
  "data": null
}
```

---

### 4. Real-Time Leaderboard
**Endpoint:** `GET /leaderboard/`  
**Authentication:** Required (Rider Bearer Token)  
**Description:** Returns real-time ranked list of top 50 riders and the requesting rider's current rank, trips count, and earnings for the selected period (`this_week`, `this_month`, or `all_time`). Powered by Redis Sorted Sets with automatic PostgreSQL failover.

**Query Parameters:**
- `period` (optional): `this_week`, `this_month` (default), or `all_time`.

**Success Response (200 OK):**
```json
{
  "period": "this_month",
  "period_key": "2026-09",
  "my_rank": 3,
  "entries": [
    {
      "rank": 1,
      "rider_id": "R-101",
      "name": "Ade Babatunde",
      "zone": "Ikeja",
      "trips_count": 45,
      "earnings": "67500.00",
      "is_me": false
    },
    {
      "rank": 2,
      "rider_id": "R-105",
      "name": "Emeka Okafor",
      "zone": "Lekki Phase 1",
      "trips_count": 42,
      "earnings": "63000.00",
      "is_me": false
    },
    {
      "rank": 3,
      "rider_id": "R-102",
      "name": "Musa Danjuma",
      "zone": "Victoria Island",
      "trips_count": 39,
      "earnings": "58500.00",
      "is_me": true
    }
  ]
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

### 10. Order Offers List
**Endpoint:** `GET /orders/offers/`  
**Authentication:** Required (Verified Rider)  
**Description:** Returns pending unassigned order offers in the rider's zone. Unverified independent riders (pending KYC review) are forbidden from viewing offers.

**Error Response (403 Forbidden - Unverified Rider):**
```json
{
  "detail": "Account is not verified or authorized. You cannot access order offers until approved."
}
```

---

### 11. Accept Order Offer
**Endpoint:** `POST /orders/offers/<uuid:offer_id>/accept/`  
**Authentication:** Required (Verified Rider)  
**Description:** Accepts a pending order offer and assigns the order to the rider. Unverified independent riders cannot accept offers.

**Error Response (403 Forbidden - Unverified Rider):**
```json
{
  "detail": "Account is not verified or authorized. You cannot access order offers until approved."
}
```

---

### 12. Toggle Duty Status
**Endpoint:** `POST /duty/`  
**Authentication:** Required (Rider)  
**Description:** Toggles the rider's duty status (`online` / `offline`). Toggling to `online` is blocked if the rider is not authorized or verified.

**Request Body:**
```json
{
  "status": "online",
  "latitude": 6.5244,
  "longitude": 3.3792
}
```

**Error Response (403 Forbidden - Unverified Rider going online):**
```json
{
  "success": false,
  "message": "Account is not verified or authorized to go online."
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

### 2. Create Order
**Endpoint:** `POST /orders/`  
**Authentication:** Required (Dispatcher Admin)  
**Description:** Creates a new order. Support for partner orders and manual price overrides.

**Partner Orders**:
- If `is_partner_order` is `true`, the merchant must have `is_partner=True` in their profile.
- `total_amount` is calculated as `partner_base_price * partner_order_count`.
- Pickup, dropoff, and receiver fields are optional for partner orders and will use defaults if omitted.

**Request Body (Partial):**
```json
{
  "pickup": "...",
  "dropoff": "...",
  "senderName": "...",
  "senderPhone": "...",
  "receiverName": "...",
  "receiverPhone": "...",
  "vehicle": "Bike",
  "packageType": "Box",
  "is_partner_order": true,
  "partner_order_count": 50,
  "file_uploaded_url": "https://..."
}
```

---

## Rider Management

### 1. List Riders
**Endpoint:** `GET /riders/`

### 2. Assign Vehicle
**Endpoint:** `POST /riders/{id}/assign_vehicle/`  
**Authentication:** Required (Dispatcher Admin)  
**Description:** Assigns or unassigns a vehicle asset to a rider.

**Permissions**: Restricted to `dispatcheradmin` only.

**Request Body**:
```json
{
  "vehicle_asset_id": "uuid" // or null to unassign
}
```

**Response**:
Returns the updated rider object.

**History Tracking**:
Every assignment/unassignment creates a `VehicleReassignment` record:
- If a vehicle is assigned to Rider A from Rider B: `from_rider=Rider B`, `to_rider=Rider A`.
- If a rider's vehicle is unassigned: `from_rider=Rider`, `to_rider=null`.
- If a rider moves from Vehicle Y to Vehicle X: Records unassignment of Y and assignment of X.
- The record captures the `admin` user who initiated the request.

### 3. Reject Rider Application (with Email Notification)
**Endpoint:** `POST /api/dispatch/riders/{id}/reject/`  
**Authentication:** Required (Dispatcher Admin)  
**Description:** Rejects a self-registered rider's onboarding application. Optionally flags specific submitted KYC documents as rejected (with individual reasons each) so the rider can review and re-upload them. Automatically sends a push notification and an HTML/text rejection email to the rider detailing the overall rejection reason, the specific rejected documents, and the reasons.

**Request Body:**
```json
{
  "reason": "Submitted KYC documents failed compliance checks.",
  "rejected_documents": [
    {
      "document_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "reason": "Driver's license photo is blurry and illegible."
    },
    {
      "document_id": "8bb96d74-1234-4562-b3fc-2c963f66afa7",
      "reason": "Vehicle insurance policy has expired."
    }
  ]
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "rider_id": "200001",
    "first_name": "Tunde",
    "last_name": "Bakare",
    "phone": "+2348123456789",
    "email": "tunde.rider@aexpress.com",
    "approval_status": "rejected",
    "is_authorized": false,
    "rejection_reason": "Submitted KYC documents failed compliance checks.",
    "documents": [
      {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "doc_type": "drivers_license",
        "status": "rejected",
        "rejection_reason": "Driver's license photo is blurry and illegible."
      }
    ]
  }
}
```

**Email Notification:**
Dispatches an email via Celery background task (`dispatcher.tasks.send_rider_rejection_email_task` with graceful direct fallback) using Mailgun and MailNow fallback:
- **Subject:** `Important Update Regarding Your Rider Application - Assured Express`
- **Content:** Outlines the review decision, the general reason, a styled table of rejected documents with corresponding rejection reasons, and step-by-step guidance on how to re-upload via the Assured Express Rider mobile app (`Profile > KYC Documents`).

---


### 3. List Vehicle Assets
**Endpoint:** `GET /vehicle-assets/`  
**Authentication:** Required (Dispatcher Admin)  
**Description:** Returns a list of all vehicle assets including their assignment, distance covered yesterday, and orders completed today.

**Key Response Fields:**
- `orders_today` (integer): Count of completed orders today for the assigned rider(s) calculated dynamically using local timezone boundaries and fallback mechanisms.
- `yesterday_orders` (integer): Count of completed orders yesterday for the assigned rider(s) calculated dynamically using strict local timezone boundaries and fallback mechanisms.
- `yesterday_distance` (decimal): Travelled GPS/odometer tracking distance (in km or specified units) covered by the asset yesterday.
- `total_yesterday_orders_distance_km` (float): Sum of `distance_km` for completed orders yesterday by the vehicle's assigned rider(s). Also aliased as `yesterday_orders_distance` and `total_yesterday_order_distance`.
- `assigned_rider` (object|null): Details of the currently assigned rider.

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
  "data": {
    "parcel": { ... },
    "statuscode": "00",
    "statusmessage": "New parcel request successful. Locker Number (5) has been reserved for you at (SmartParcel Sterling Bank Adeola Odeku)."
  }
}
```

**Error Response (502 Bad Gateway - API Error / Validation Error / Business Logic Error):**
```json
{
  "status": "error",
  "message": "No (Medium) locker available at (SmartParcel Sterling Bank Adeola Odeku).",
  "data": {}
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

---

## Places API (Google Places / Fallbacks & Session Usage Tracking)
**Base URL:** `/api/orders/places/`

### 1. Places Autocomplete
**Endpoint:** `GET /autocomplete/`  
**Authentication:** Required (Merchant Token or API Key)  
**Description:** Get location autocomplete suggestions using Google Places API (with fallback chain: Geoapify -> Mapbox -> AWS Location Service). Automatically records session token usage in GoogleAutoCompleteSessionUsage (status: IN_PROGRESS, price per session: $0.005).

**Query Parameters:**
- `q` (required): The partial query text to search for.
- `session_token` (optional): A UUID string to group suggestions and details retrieve requests for Google / Mapbox session billing.

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Autocomplete suggestions retrieved successfully From Google",
  "data": [
    {
      "place_id": "google:ChIJb_google_place_id",
      "description": "15a Kunle Ogunba St, Lekki, Lagos, Nigeria",
      "is_google": true,
      "structured_formatting": {
        "main_text": "15a Kunle Ogunba St",
        "secondary_text": "Lekki, Lagos, Nigeria"
      }
    }
  ],
  "status_code": 200
}
```

---

### 2. Place Details
**Endpoint:** `GET /details/`  
**Authentication:** Required (Merchant Token or API Key)  
**Description:** Retrieve the detailed formatted address and coordinates for a given PlaceId (supports `google:`, `geoapify:`, `mapbox:`, or `aws:` prefixes). When called with session_token for a Google place, marks the GoogleAutoCompleteSessionUsage as RESOLVED with the resolved place_id and timestamp.

**Query Parameters:**
- `place_id` (required): The PlaceId returned by the autocomplete suggestion (e.g. `google:ChIJ...`).
- `session_token` (optional): A UUID string matching the autocomplete session_token.

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Place details retrieved successfully",
  "data": {
    "formatted_address": "15a Kunle Ogunba St, Lekki, Lagos, Nigeria",
    "lat": 6.4399005,
    "lng": 3.4701005
  },
  "status_code": 200
}
```

---

### 3. Reverse Geocode Coordinates
**Endpoint:** `GET /reverse-geocode/`  
**Authentication:** Required (Merchant Token or API Key)  
**Description:** Reverse geocode coordinates to a human-readable address.

**Query Parameters:**
- `lat` (required): Latitude float.
- `lng` (required): Longitude float.

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Coordinates reverse geocoded successfully",
  "data": {
    "address": "Lekki Peninsula, Victoria Island, Lagos, NGA"
  },
  "status_code": 200
}
```

---

### 4. Geocode Address
**Endpoint:** `GET /geocode/`  
**Authentication:** Required (Merchant Token or API Key)  
**Description:** Geocode an address string to coordinates.

**Query Parameters:**
- `address` (required): The address string to geocode.

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Address geocoded successfully",
  "data": {
    "lat": 6.5244,
    "lng": 3.3792
  },
  "status_code": 200
}
```

---

## DISPATCHER AFFILIATION & MERCHANT COMMISSION ENDPOINTS

### 1. Get Merchant Affiliation Status
```http
GET /api/auth/merchant/affiliation/
GET /api/merchant/affiliation/
Description: Retrieves the current dispatcher affiliation details for the authenticated merchant profile.
Authentication: Required (Merchant)
Response (200 OK):
  {
    "status": "success",
    "message": "Merchant affiliation retrieved successfully",
    "data": {
      "is_affiliated": true,
      "affiliated_at": "2026-10-15T12:00:00Z",
      "dispatcher": {
        "id": "d44bd075-412f-4d37-8dc0-7df81320ddcd",
        "name": "Ikeja Hub Dispatcher",
        "company_name": "Ikeja Hub Logistics",
        "role": "hub_captain",
        "role_display": "Hub Captain",
        "affiliation_code": "HUB001",
        "hub_name": "Ikeja Hub",
        "zone_name": "Ikeja"
      }
    },
    "status_code": 200
  }
```

### 2. Affiliate Merchant to Dispatcher
```http
POST /api/auth/merchant/affiliation/
POST /api/merchant/affiliation/
Description: Affiliates the authenticated merchant to a dispatcher using their unique affiliation code.
Authentication: Required (Merchant)
Request Body:
  {
    "affiliation_code": "HUB001"
  }
Response (200 OK):
  {
    "status": "success",
    "message": "Successfully affiliated with dispatcher Ikeja Hub Logistics",
    "data": {
      "is_affiliated": true,
      "affiliated_at": "2026-10-15T12:00:00Z",
      "dispatcher": {
        "id": "d44bd075-412f-4d37-8dc0-7df81320ddcd",
        "name": "Ikeja Hub Dispatcher",
        "company_name": "Ikeja Hub Logistics",
        "role": "hub_captain",
        "role_display": "Hub Captain",
        "affiliation_code": "HUB001",
        "hub_name": "Ikeja Hub",
        "zone_name": "Ikeja"
      }
    },
    "status_code": 200
  }
```

### 3. List Affiliated Merchants (Dispatcher View)
```http
GET /api/dispatch/affiliation/merchants/
Description: Lists all merchants affiliated to the authenticated dispatcher with pagination, search, and activity counts.
Authentication: Required (Dispatcher)
Query Parameters:
  - page (optional): Page number (default: 1)
  - page_size (optional): Items per page (default: 20)
  - search (optional): Filter by merchant ID, business name, phone, or email
Response (200 OK):
  {
    "status": "success",
    "message": "Affiliated merchants retrieved successfully",
    "data": {
      "count": 12,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 105,
          "merchant_id": "261603",
          "name": "Acme Ventures",
          "email": "acme@example.com",
          "phone": "+2348011112222",
          "business_name": "Acme Retail Ltd",
          "merchant_type": "Retail",
          "status": "active",
          "affiliated_at": "2026-10-15T12:00:00Z",
          "total_orders": 34,
          "monthly_orders": 8,
          "monthly_commission": 24000.0
        }
      ]
    },
    "status_code": 200
  }
```

### 4. Dispatcher Affiliation Summary
```http
GET /api/dispatch/affiliation/summary/
Description: Retrieves aggregated performance and earnings for the dispatcher, including affiliated riders, affiliated merchants, and monthly commission totals.
Authentication: Required (Dispatcher)
Response (200 OK):
  {
    "status": "success",
    "message": "Affiliation summary retrieved successfully",
    "data": {
      "dispatcher_id": "d44bd075-412f-4d37-8dc0-7df81320ddcd",
      "affiliation_code": "HUB001",
      "role": "hub_captain",
      "role_display": "Hub Captain",
      "monthly_commission": 45000.0,
      "previous_month_commission": 30000.0,
      "total_commission_earned": 75000.0,
      "commission_per_order": 3000.0,
      "affiliated_riders_count": 5,
      "total_affiliated_riders": 5,
      "active_riders_this_month": 3,
      "affiliated_merchants_count": 8,
      "total_affiliated_merchants": 8,
      "active_merchants_this_month": 4,
      "current_month": "October 2026",
      "currency": "NGN"
    },
    "status_code": 200
  }
```

### 5. Dispatcher Commission History
```http
GET /api/dispatch/affiliation/commissions/
Description: Lists ledgered commission records for the authenticated dispatcher with optional source and merchant filtering.
Authentication: Required (Dispatcher)
Query Parameters:
  - page (optional): Page number (default: 1)
  - page_size (optional): Items per page (default: 20)
  - month (optional): Filter by month string (format: YYYY-MM)
  - rider_id (optional): Filter by rider ID
  - merchant_id (optional): Filter by merchant ID
  - source (optional): Filter by affiliation source ('rider' or 'merchant')
Response (200 OK):
  {
    "status": "success",
    "message": "Commissions retrieved successfully",
    "data": {
      "count": 15,
      "results": [
        {
          "id": "b968fc24-...",
          "order_number": "6158045",
          "amount": 3000.0,
          "affiliation_source": "merchant",
          "rider_id": null,
          "rider_name": null,
          "merchant_id": "261603",
          "merchant_name": "Acme Retail Ltd",
          "month_year": "2026-10",
          "description": "Affiliation commission for completed order #6158045 from merchant 261603",
          "created_at": "2026-10-15T14:30:00Z"
        }
      ]
    },
    "status_code": 200
  }
```

### 6. Verify Affiliation Code (Public)
```http
GET /api/auth/affiliation/verify/?code=HUB001
GET /api/merchant/affiliation/verify/?code=HUB001
GET /api/riders/affiliation/verify/?code=HUB001
GET /api/affiliation/verify/?code=HUB001
POST /api/auth/affiliation/verify/
POST /api/merchant/affiliation/verify/
POST /api/riders/affiliation/verify/
POST /api/affiliation/verify/
Description: Validates a dispatcher affiliation code and returns the dispatcher's details (name, phone, role, hub, zone) without requiring authentication. Used during rider/merchant onboarding and profile linking.
Authentication: None (Public - AllowAny)

Query Parameters (GET):
  - code or affiliation_code (required): The affiliation code to verify (e.g. 'HUB001'). Case-insensitive.

Request Body (POST):
  {
    "affiliation_code": "HUB001"
  }
  // Or alias: {"code": "HUB001"}

Response (200 OK):
  {
    "status": "success",
    "message": "Affiliation code is valid.",
    "data": {
      "is_valid": true,
      "affiliation_code": "HUB001",
      "dispatcher_id": "d44bd075-412f-4d37-8dc0-7df81320ddcd",
      "name": "Alice Hub Captain",
      "phone": "+2348011110001",
      "role": "hub_captain",
      "role_display": "Hub Captain",
      "hub_name": "Ikeja Central Hub",
      "zone_name": "Ikeja Zone"
    },
    "status_code": 200
  }

Error Response (400 Bad Request):
  {
    "status": "error",
    "message": "Invalid affiliation code. No active dispatcher found with this code.",
    "data": {},
    "status_code": 400
  }
```
