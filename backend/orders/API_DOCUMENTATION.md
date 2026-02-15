# Order Management API Documentation

## Overview

The Order Management API provides endpoints for creating and managing delivery orders in three modes:
- **Quick Send**: Single pickup, single delivery
- **Multi-Drop**: Single pickup, multiple deliveries
- **Bulk Import**: Single pickup, multiple deliveries (imported from CSV/text/OCR)

All endpoints require JWT authentication via the `Authorization: Bearer <token>` header.

---

## Base URL

```
http://127.0.0.1:8000/api/orders/
```

---

## Endpoints

### 1. Get Available Vehicles

**GET** `/api/orders/vehicles/`

Get all available vehicle types with pricing information.

**Authentication**: Required

**Response** (200 OK):
```json
{
  "success": true,
  "vehicles": [
    {
      "id": 1,
      "name": "Bike",
      "max_weight_kg": 10,
      "base_price": "1200.00",
      "description": "Motorcycle delivery for small packages up to 10kg",
      "is_active": true
    },
    {
      "id": 2,
      "name": "Car",
      "max_weight_kg": 70,
      "base_price": "4500.00",
      "description": "Car delivery for medium packages up to 70kg",
      "is_active": true
    },
    {
      "id": 3,
      "name": "Van",
      "max_weight_kg": 600,
      "base_price": "12000.00",
      "description": "Van delivery for large packages up to 600kg",
      "is_active": true
    }
  ]
}
```

---

### 2. Create Quick Send Order

**POST** `/api/orders/quick-send/`

Create a Quick Send order with a single delivery.

**Authentication**: Required

**Request Body**:
```json
{
  "pickup_address": "27A Idowu Martins St, Victoria Island, Lagos",
  "sender_name": "Yetunde Igbene",
  "sender_phone": "08051832508",
  "dropoff_address": "24 Harvey Rd, Sabo Yaba, Lagos",
  "receiver_name": "Adebayo Johnson",
  "receiver_phone": "08034567890",
  "vehicle": "Bike",
  "payment_method": "wallet",
  "package_type": "Box",
  "notes": "Handle with care",
  "scheduled_pickup_time": "2024-02-14T15:00:00Z"
}
```

**Field Descriptions**:
- `pickup_address` (required): Pickup location address
- `sender_name` (required): Name of sender
- `sender_phone` (required): Phone number of sender
- `dropoff_address` (required): Delivery destination address
- `receiver_name` (required): Name of receiver
- `receiver_phone` (required): Phone number of receiver
- `vehicle` (required): Vehicle type - "Bike", "Car", or "Van"
- `payment_method` (optional): "wallet" (default), "cash_on_pickup", or "receiver_pays"
- `package_type` (optional): "Box" (default), "Envelope", "Fragile", "Food", "Document", or "Other"
- `notes` (optional): Additional delivery instructions
- `scheduled_pickup_time` (optional): ISO 8601 datetime for scheduled pickup

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Quick Send order created successfully!",
  "order": {
    "id": "uuid-here",
    "order_number": "6158000",
    "user_business_name": "AX Express Admin",
    "mode": "quick",
    "vehicle_name": "Bike",
    "vehicle_price": "1200.00",
    "pickup_address": "27A Idowu Martins St, Victoria Island, Lagos",
    "sender_name": "Yetunde Igbene",
    "sender_phone": "08051832508",
    "payment_method": "wallet",
    "total_amount": "1200.00",
    "status": "Pending",
    "created_at": "2024-02-14T12:00:00Z",
    "updated_at": "2024-02-14T12:00:00Z",
    "scheduled_pickup_time": null,
    "notes": "Handle with care",
    "delivery_count": 1,
    "deliveries": [
      {
        "id": "uuid-here",
        "dropoff_address": "24 Harvey Rd, Sabo Yaba, Lagos",
        "receiver_name": "Adebayo Johnson",
        "receiver_phone": "08034567890",
        "package_type": "Box",
        "notes": "Handle with care",
        "status": "Pending",
        "sequence": 1,
        "created_at": "2024-02-14T12:00:00Z",
        "delivered_at": null
      }
    ]
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "success": false,
  "errors": {
    "vehicle": ["Vehicle 'InvalidVehicle' not found or inactive."]
  }
}
```

---

### 3. Create Multi-Drop Order

**POST** `/api/orders/multi-drop/`

Create a Multi-Drop order with multiple deliveries from a single pickup location.

**Authentication**: Required

**Request Body**:
```json
{
  "pickup_address": "15 Admiralty Way, Lekki Phase 1, Lagos",
  "sender_name": "Yetunde Igbene",
  "sender_phone": "08051832508",
  "vehicle": "Car",
  "payment_method": "wallet",
  "deliveries": [
    {
      "dropoff_address": "42 Allen Avenue, Ikeja, Lagos",
      "receiver_name": "Funke Adeyemi",
      "receiver_phone": "09012345678",
      "package_type": "Box",
      "notes": "First delivery"
    },
    {
      "dropoff_address": "10 Broad St, Lagos Island",
      "receiver_name": "Chidi Obi",
      "receiver_phone": "07011223344",
      "package_type": "Envelope",
      "notes": "Second delivery"
    },
    {
      "dropoff_address": "33 Opebi Rd, Ikeja, Lagos",
      "receiver_name": "Blessing Nwosu",
      "receiver_phone": "08155667788",
      "package_type": "Fragile",
      "notes": "Third delivery - fragile"
    }
  ],
  "notes": "Multi-drop delivery",
  "scheduled_pickup_time": null
}
```

**Field Descriptions**:
- `pickup_address` (required): Pickup location address
- `sender_name` (required): Name of sender
- `sender_phone` (required): Phone number of sender
- `vehicle` (required): Vehicle type - "Bike", "Car", or "Van"
- `payment_method` (optional): "wallet" (default), "cash_on_pickup", or "receiver_pays"
- `deliveries` (required): Array of delivery objects (minimum 1)
  - `dropoff_address` (required): Delivery destination address
  - `receiver_name` (required): Name of receiver
  - `receiver_phone` (required): Phone number of receiver
  - `package_type` (optional): "Box" (default), "Envelope", "Fragile", "Food", "Document", or "Other"
  - `notes` (optional): Delivery-specific notes
- `notes` (optional): Order-level notes
- `scheduled_pickup_time` (optional): ISO 8601 datetime for scheduled pickup

**Pricing**: Total amount = vehicle base price × number of deliveries

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Multi-Drop order created with 3 deliveries!",
  "order": {
    "id": "uuid-here",
    "order_number": "6158001",
    "mode": "multi",
    "vehicle_name": "Car",
    "vehicle_price": "4500.00",
    "total_amount": "13500.00",
    "delivery_count": 3,
    "deliveries": [...]
  }
}
```

---

### 4. Create Bulk Import Order

**POST** `/api/orders/bulk-import/`

Create a Bulk Import order with multiple deliveries (typically from CSV/text/OCR import).

**Authentication**: Required

**Request Body**: Same structure as Multi-Drop

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Bulk Import order created with 5 deliveries!",
  "order": {
    "id": "uuid-here",
    "order_number": "6158002",
    "mode": "bulk",
    "total_amount": "60000.00",
    "delivery_count": 5
  }
}
```

---

### 5. Get All Orders

**GET** `/api/orders/`

Get all orders for the authenticated user with optional filtering.

**Authentication**: Required

**Query Parameters**:
- `status` (optional): Filter by status - "Pending", "Assigned", "Started", "Done", "CustomerCanceled", "RiderCanceled", "Failed"
- `mode` (optional): Filter by mode - "quick", "multi", "bulk"
- `limit` (optional): Limit number of results (integer)

**Examples**:
```
GET /api/orders/
GET /api/orders/?status=Pending
GET /api/orders/?mode=quick
GET /api/orders/?status=Done&limit=10
```

**Response** (200 OK):
```json
{
  "success": true,
  "count": 3,
  "orders": [
    {
      "id": "uuid-here",
      "order_number": "6158002",
      "user_business_name": "AX Express Admin",
      "mode": "bulk",
      "vehicle_name": "Van",
      "vehicle_price": "12000.00",
      "pickup_address": "24 Alara St, Iwaya, Lagos",
      "sender_name": "Yetunde Igbene",
      "sender_phone": "08051832508",
      "payment_method": "cash_on_pickup",
      "total_amount": "60000.00",
      "status": "Pending",
      "created_at": "2024-02-14T12:00:00Z",
      "updated_at": "2024-02-14T12:00:00Z",
      "delivery_count": 5,
      "deliveries": [...]
    }
  ]
}
```

---

### 6. Get Order Details

**GET** `/api/orders/<order_number>/`

Get detailed information about a specific order.

**Authentication**: Required

**Example**:
```
GET /api/orders/6158000/
```

**Response** (200 OK):
```json
{
  "success": true,
  "order": {
    "id": "uuid-here",
    "order_number": "6158000",
    "mode": "quick",
    "status": "Pending",
    "vehicle_name": "Bike",
    "pickup_address": "27A Idowu Martins St, Victoria Island, Lagos",
    "deliveries": [...]
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "message": "Order not found."
}
```

---

### 7. Get Order Statistics

**GET** `/api/orders/stats/`

Get order statistics for the authenticated user's dashboard.

**Authentication**: Required

**Response** (200 OK):
```json
{
  "success": true,
  "stats": {
    "total_orders": 3,
    "pending_orders": 3,
    "completed_orders": 0,
    "canceled_orders": 0,
    "total_spent": 0,
    "average_cost": 0
  }
}
```

---

## Order Status Flow

```
Pending → Assigned → Started → Done
         ↓
    CustomerCanceled / RiderCanceled / Failed
```

**Status Descriptions**:
- `Pending`: Order created, waiting for rider assignment
- `Assigned`: Rider assigned to order
- `Started`: Rider has started the delivery
- `Done`: Delivery completed successfully
- `CustomerCanceled`: Canceled by customer
- `RiderCanceled`: Canceled by rider
- `Failed`: Delivery failed

---

## Payment Methods

- **wallet**: Deduct from merchant's wallet balance (prepaid)
- **cash_on_pickup**: Merchant pays rider in cash at pickup
- **receiver_pays**: Receiver pays on delivery (COD)

---

## Package Types

- **Box**: Standard box package
- **Envelope**: Document envelope
- **Fragile**: Fragile items requiring special care
- **Food**: Food delivery
- **Document**: Important documents
- **Other**: Other package types

---

## Error Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Testing

Run the test script to verify all endpoints:

```bash
cd backend
source venv/bin/activate
python test_orders_api.py
```

