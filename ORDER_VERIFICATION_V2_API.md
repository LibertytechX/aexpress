# Order Pickup & Delivery Verification V2 API Documentation

## Overview

The V2 verification endpoints eliminate reliance on GPS location proximity checks for rider order pickup and delivery completion by introducing secure 6-digit numeric verification codes.

- **Pickup Code (`order.pickup_code`)**: Automatically generated 6-digit numeric code on `Order`. Shared by the merchant/sender with the rider at pickup.
- **Drop Code (`delivery.drop_code`)**: Automatically generated 6-digit numeric code on `Delivery`. Shared by the recipient/customer with the rider at drop-off.
- **Brute-Force Protection**: Capped at **5 failed attempts** per order/delivery. Exceeding 5 attempts locks verification and requires administrative support.
- **Idempotency**: Retrying completed pickup or drop-off requests returns `200 OK` with the current state.
- **Automated Lifecycle**: Verifying the final delivery triggers atomic state updates (`Done`), rider commission earnings allocation to their wallet, push notifications, and `order-completed` webhook triggers.

---

## Authentication & Authorization

All endpoints require standard Bearer token authentication and the authenticated user must be a Rider:
```http
Authorization: Bearer <rider_jwt_access_token>
Content-Type: application/json
```

---

## Endpoints Summary

| Method | Endpoint | Internal Name | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/orders/v2/pickup/` | `order_pickup_v2` | Verifies merchant 6-digit pickup code and marks order as `PickedUp`. |
| `POST` | `/api/orders/v2/complete/` | `order_complete_v2` | Verifies recipient 6-digit drop code for single-delivery order and completes order (`Done`). |
| `POST` | `/api/orders/v2/delivery/<delivery_id>/deliver/` | `delivery_deliver_v2` | Verifies recipient 6-digit drop code for a specific stop in multi-drop order. |

---

## Endpoint Details

### 1. Confirm Order Pickup (V2)

Verifies the 6-digit `pickup_code` provided by the merchant and marks the order as picked up.

- **Route:** `POST /api/orders/v2/pickup/`
- **View:** `OrderPickupV2View` ([`backend/orders/v2_views.py`](file:///Users/mac/Liberty/aexpress/backend/orders/v2_views.py#L149-L279))
- **URL Name:** `orders:order_pickup_v2`

#### Request Body
```json
{
  "order_number": "6158001",
  "pickup_code": "123456"
}
```

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `order_number` | string | Yes | Unique order number. Max length: 20. |
| `pickup_code` | string | Yes | Exactly 6 numeric digits provided by merchant. |

#### Success Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Order picked up successfully.",
  "data": {
    "order_number": "6158001",
    "status": "PickedUp",
    "picked_up_at": "2026-10-30T08:15:30.123456Z"
  },
  "status_code": 200
}
```

#### Error Responses
- **`400 Bad Request` (Invalid format or mismatch):**
  ```json
  {
    "status": "error",
    "message": "Incorrect pickup code. 4 attempt(s) remaining.",
    "data": {},
    "status_code": 400
  }
  ```
- **`400 Bad Request` (Locked out):**
  ```json
  {
    "status": "error",
    "message": "Pickup verification is locked due to too many failed attempts (maximum 5). Please contact support.",
    "data": {},
    "status_code": 400
  }
  ```
- **`400 Bad Request` (Invalid status transition):**
  ```json
  {
    "status": "error",
    "message": "Cannot pick up order in current status: CustomerCanceled",
    "data": {},
    "status_code": 400
  }
  ```
- **`403 Forbidden` (Not assigned rider / invalid profile):**
  ```json
  {
    "status": "error",
    "message": "You are not the assigned rider for this order.",
    "data": {},
    "status_code": 403
  }
  ```
- **`404 Not Found`:**
  ```json
  {
    "status": "error",
    "message": "Order not found.",
    "data": {},
    "status_code": 404
  }
  ```

---

### 2. Complete Single-Delivery Order (V2)

Verifies the recipient's 6-digit `drop_code` for a single-delivery order (Quick Send), marks the delivery as `Delivered`, advances the order status to `Done`, and initiates rider commission credit to the rider wallet.

- **Route:** `POST /api/orders/v2/complete/`
- **View:** `OrderCompleteV2View` ([`backend/orders/v2_views.py`](file:///Users/mac/Liberty/aexpress/backend/orders/v2_views.py#L411-L536))
- **URL Name:** `orders:order_complete_v2`

#### Request Body
```json
{
  "order_number": "6158001",
  "drop_code": "654321"
}
```

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `order_number` | string | Yes | Unique order number. Max length: 20. |
| `drop_code` | string | Yes | Exactly 6 numeric digits received from the recipient. |

#### Success Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Order delivery completed successfully.",
  "data": {
    "order_number": "6158001",
    "status": "Done",
    "all_delivered": true
  },
  "status_code": 200
}
```

#### Error Responses
- **`400 Bad Request` (Incorrect drop code):**
  ```json
  {
    "status": "error",
    "message": "Incorrect drop code. 3 attempt(s) remaining.",
    "data": {},
    "status_code": 400
  }
  ```
- **`400 Bad Request` (Locked out):**
  ```json
  {
    "status": "error",
    "message": "Delivery verification is locked due to too many failed attempts (maximum 5). Please contact support.",
    "data": {},
    "status_code": 400
  }
  ```
- **`403 Forbidden`:**
  ```json
  {
    "status": "error",
    "message": "You are not the assigned rider for this order.",
    "data": {},
    "status_code": 403
  }
  ```
- **`404 Not Found`:**
  ```json
  {
    "status": "error",
    "message": "Order not found.",
    "data": {},
    "status_code": 404
  }
  ```

---

### 3. Deliver Multi-Drop Stop (V2)

Verifies the recipient's 6-digit `drop_code` for a specific delivery stop within a multi-drop order. If other pending stops remain, the order status remains `Fulfilling`. If this is the final pending stop, the order transitions to `Done` and earnings are allocated.

- **Route:** `POST /api/orders/v2/delivery/<delivery_id>/deliver/`
- **View:** `DeliveryCompleteV2View` ([`backend/orders/v2_views.py`](file:///Users/mac/Liberty/aexpress/backend/orders/v2_views.py#L281-L409))
- **URL Name:** `orders:delivery_deliver_v2`

#### Path Parameters
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `delivery_id` | UUID string | Yes | UUID of the specific `Delivery` stop. |

#### Request Body
```json
{
  "drop_code": "654321"
}
```

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `drop_code` | string | Yes | Exactly 6 numeric digits received from the recipient of this stop. |

#### Success Response (`200 OK` - Intermediate Stop Completed)
```json
{
  "status": "success",
  "message": "Delivery completed successfully.",
  "data": {
    "delivery_id": "c1f7b7e5-1234-5678-90ab-cdef12345678",
    "status": "Delivered",
    "delivered_at": "2026-10-30T08:30:15.654321Z",
    "order_number": "6158001",
    "order_status": "Fulfilling",
    "all_delivered": false
  },
  "status_code": 200
}
```

#### Success Response (`200 OK` - Final Stop Completed)
```json
{
  "status": "success",
  "message": "Delivery completed successfully.",
  "data": {
    "delivery_id": "c1f7b7e5-1234-5678-90ab-cdef12345678",
    "status": "Delivered",
    "delivered_at": "2026-10-30T08:45:00.000000Z",
    "order_number": "6158001",
    "order_status": "Done",
    "all_delivered": true
  },
  "status_code": 200
}
```

#### Error Responses
- **`400 Bad Request` (Invalid delivery status):**
  ```json
  {
    "status": "error",
    "message": "Cannot complete delivery in current status: Canceled",
    "data": {},
    "status_code": 400
  }
  ```
- **`400 Bad Request` (Incorrect drop code):**
  ```json
  {
    "status": "error",
    "message": "Incorrect drop code. 2 attempt(s) remaining.",
    "data": {},
    "status_code": 400
  }
  ```
- **`403 Forbidden`:**
  ```json
  {
    "status": "error",
    "message": "You are not the assigned rider for this delivery.",
    "data": {},
    "status_code": 403
  }
  ```
- **`404 Not Found`:**
  ```json
  {
    "status": "error",
    "message": "Delivery not found.",
    "data": {},
    "status_code": 404
  }
  ```

