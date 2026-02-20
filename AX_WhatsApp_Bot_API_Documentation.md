# AX WhatsApp Bot API Documentation

## Overview

The AX WhatsApp Bot API provides a complete backend for managing delivery orders via WhatsApp. It uses API key authentication and phone-based merchant identification.

## Base URL

```
https://www.orders.axpress.net/api/bot/
```

## Authentication

### API Key Authentication

All requests require an API key passed via the `X-API-Key` header.

**Production API Key:**
```
sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0
```

### Merchant Identification

Merchant-specific endpoints require the merchant's phone number via the `X-Merchant-Phone` header.

**Phone Format:** `2348012345678` (no + or spaces)

### Example Headers

```http
X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0
X-Merchant-Phone: 2348098765432
Content-Type: application/json
```

---

## Endpoints

### 1. Merchant Lookup

**Endpoint:** `GET /api/bot/lookup/`

**Description:** Lookup a merchant by phone number.

**Authentication:** API Key only (no merchant phone required)

**Query Parameters:**
- `phone` (required): Merchant phone number

**Example Request:**
```bash
curl -X GET "https://www.orders.axpress.net/api/bot/lookup/?phone=2348012345678" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0"
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "business_name": "Test Logistics Ltd",
    "contact_name": "Chidi Okafor",
    "phone": "2348012345678",
    "email": "merchant@example.com",
    "wallet_balance": 15000.00
  },
  "bot_response": "Welcome back, Chidi! Your balance is ₦15,000."
}
```

**Not Found Response (200):**
```json
{
  "success": false,
  "message": "Merchant not found",
  "bot_response": "I don't have this number on file yet. Want to sign up? Just tell me your business name."
}
```

---

### 2. Quick Signup

**Endpoint:** `POST /api/bot/signup/`

**Description:** Passwordless signup for WhatsApp bot users.

**Authentication:** API Key only (no merchant phone required)

**Request Body:**
```json
{
  "phone": "2348098765432",
  "business_name": "Test Logistics Ltd",
  "contact_name": "Chidi Okafor"
}
```

**Example Request:**
```bash
curl -X POST "https://www.orders.axpress.net/api/bot/signup/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "2348098765432",
    "business_name": "Test Logistics Ltd",
    "contact_name": "Chidi Okafor"
  }'
```

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "business_name": "Test Logistics Ltd",
    "contact_name": "Chidi Okafor",
    "phone": "2348098765432",
    "email": "whatsapp_2348098765432@axpress.bot",
    "wallet_balance": 0.0
  },
  "bot_response": "Sharp, Chidi Okafor from Test Logistics Ltd — you're in ✅\nYour wallet starts at ₦0. Ready to create your first delivery?"
}
```

---

### 3. Dashboard Summary

**Endpoint:** `GET /api/bot/summary/`

**Description:** Get merchant dashboard summary in one call.

**Authentication:** API Key + Merchant Phone

**Example Request:**
```bash
curl -X GET "https://www.orders.axpress.net/api/bot/summary/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "X-Merchant-Phone: 2348098765432"
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "wallet_balance": 20000.0,
    "active_orders_count": 2,
    "completed_today": 5,
    "spent_today": 12500.0,
    "recent_orders": [
      {
        "order_number": "6158010",
        "status": "pending",
        "summary": "6158010 — pending ⏳\nVictoria Island → Ikeja | ₦6,707"
      }
    ],
    "last_transaction": {
      "reference": "TXN-ABC123",
      "type": "credit",
      "amount": "20000.00",
      "formatted_amount": "₦20,000"
    }
  },
  "bot_response": "You've got ₦20,000 in your wallet and 2 active orders."
}
```

---

### 4. Get Price Quote

**Endpoint:** `POST /api/bot/orders/get-price/`

**Description:** Calculate delivery price for a route using Google Maps.

**Authentication:** API Key + Merchant Phone

**Request Body:**
```json
{
  "pickup_address": "Victoria Island, Lagos",
  "dropoff_address": "Ikeja City Mall, Lagos"
}
```

**Example Request:**
```bash
curl -X POST "https://www.orders.axpress.net/api/bot/orders/get-price/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "X-Merchant-Phone: 2348098765432" \
  -H "Content-Type: application/json" \
  -d '{
    "pickup_address": "Victoria Island, Lagos",
    "dropoff_address": "Ikeja City Mall, Lagos"
  }'
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "prices": [
      {
        "vehicle": "Bike",
        "price": 6707.25,
        "formatted_price": "₦6,707",
        "distance_km": 29.8,
        "duration_minutes": 38
      },
      {
        "vehicle": "Car",
        "price": 20705.0,
        "formatted_price": "₦20,705",
        "distance_km": 29.8,
        "duration_minutes": 38
      }
    ],
    "distance_km": 29.81,
    "duration_minutes": 38
  },
  "bot_response": "Here are your options:\nBike: ₦6,707\nCar: ₦20,705\nVan: ₦36,448\n\n(29.8km, ~38 mins)"
}
```

---

### 5. Create Order

**Endpoint:** `POST /api/bot/orders/create/`

**Description:** Create a new delivery order.

**Authentication:** API Key + Merchant Phone

**Request Body:**
```json
{
  "pickup_address": "Victoria Island, Lagos",
  "dropoff_address": "Ikeja City Mall, Lagos",
  "vehicle_type": "Bike",
  "pickup_contact_name": "Chidi",
  "pickup_contact_phone": "2348098765432",
  "dropoff_contact_name": "Emeka",
  "dropoff_contact_phone": "2348087654321",
  "payment_method": "wallet",
  "package_type": "Box",
  "notes": "Handle with care"
}
```

**Field Descriptions:**
- `pickup_address` (required): Pickup location
- `dropoff_address` (required): Dropoff location
- `vehicle_type` (required): `Bike`, `Car`, or `Van`
- `pickup_contact_name` (required): Sender name
- `pickup_contact_phone` (required): Sender phone
- `dropoff_contact_name` (required): Receiver name
- `dropoff_contact_phone` (required): Receiver phone
- `payment_method` (required): `wallet`
- `package_type` (optional): `Box`, `Envelope`, `Fragile`, `Food`, `Document`, `Other`
- `notes` (optional): Delivery notes

**Example Request:**
```bash
curl -X POST "https://www.orders.axpress.net/api/bot/orders/create/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "X-Merchant-Phone: 2348098765432" \
  -H "Content-Type: application/json" \
  -d '{
    "pickup_address": "Victoria Island, Lagos",
    "dropoff_address": "Ikeja City Mall, Lagos",
    "vehicle_type": "Bike",
    "pickup_contact_name": "Chidi",
    "pickup_contact_phone": "2348098765432",
    "dropoff_contact_name": "Emeka",
    "dropoff_contact_phone": "2348087654321",
    "payment_method": "wallet"
  }'
```

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "order_number": "6158010",
    "status": "pending",
    "status_display": "pending",
    "mode": "quick_send",
    "pickup_address": "Victoria Island, Lagos",
    "sender_name": "Chidi",
    "sender_phone": "2348098765432",
    "vehicle_name": "Bike",
    "total_amount": "6707.25",
    "formatted_amount": "₦6,707",
    "created_at": "2026-02-18T20:39:03.719455Z",
    "summary": "6158010 — pending ⏳\nVictoria Island → Ikeja | ₦6,707"
  },
  "bot_response": "Order created! 6158010 — ₦6,707\nWe'll notify you when a rider picks it up."
}
```

**Error Response - Insufficient Balance (400):**
```json
{
  "success": false,
  "message": "Insufficient wallet balance",
  "bot_response": "Your wallet balance (₦2,000) is not enough for this delivery (₦6,707). Please fund your wallet."
}
```

---

### 6. List Orders

**Endpoint:** `GET /api/bot/orders/`

**Description:** Get list of merchant's orders.

**Authentication:** API Key + Merchant Phone

**Example Request:**
```bash
curl -X GET "https://www.orders.axpress.net/api/bot/orders/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "X-Merchant-Phone: 2348098765432"
```

**Success Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "order_number": "6158010",
      "status": "pending",
      "status_display": "pending",
      "mode": "quick_send",
      "pickup_address": "Victoria Island, Lagos",
      "sender_name": "Chidi",
      "sender_phone": "2348098765432",
      "vehicle_name": "Bike",
      "total_amount": "6707.25",
      "formatted_amount": "₦6,707",
      "created_at": "2026-02-18T20:39:03.719455Z",
      "summary": "6158010 — pending ⏳\nVictoria Island → Ikeja | ₦6,707"
    }
  ],
  "bot_response": "You have 1 order."
}
```

---

### 7. Order Detail

**Endpoint:** `GET /api/bot/orders/{order_number}/`

**Description:** Get details of a specific order.

**Authentication:** API Key + Merchant Phone

**URL Parameters:**
- `order_number`: The order number to retrieve

**Example Request:**
```bash
curl -X GET "https://www.orders.axpress.net/api/bot/orders/6158010/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "X-Merchant-Phone: 2348098765432"
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "order_number": "6158010",
    "status": "pending",
    "status_display": "pending",
    "mode": "quick_send",
    "pickup_address": "Victoria Island, Lagos",
    "sender_name": "Chidi",
    "sender_phone": "2348098765432",
    "vehicle_name": "Bike",
    "total_amount": "6707.25",
    "formatted_amount": "₦6,707",
    "created_at": "2026-02-18T20:39:03.719455Z",
    "summary": "6158010 — pending ⏳\nVictoria Island → Ikeja | ₦6,707"
  },
  "bot_response": "6158010 — pending ⏳\nVictoria Island → Ikeja | ₦6,707"
}
```

**Error Response - Not Found (404):**
```json
{
  "success": false,
  "message": "Order not found",
  "bot_response": "I couldn't find that order."
}
```

---

### 8. Cancel Order

**Endpoint:** `POST /api/bot/orders/{order_number}/cancel/`

**Description:** Cancel an order and refund to wallet.

**Authentication:** API Key + Merchant Phone

**URL Parameters:**
- `order_number`: The order number to cancel

**Example Request:**
```bash
curl -X POST "https://www.orders.axpress.net/api/bot/orders/6158010/cancel/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "X-Merchant-Phone: 2348098765432"
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "order_number": "6158010",
    "refund_amount": 6707.25,
    "new_balance": 20000.0
  },
  "bot_response": "Order 6158010 cancelled. ₦6,707 refunded to your wallet."
}
```

**Error Response - Cannot Cancel (400):**
```json
{
  "success": false,
  "message": "Cannot cancel order in current status",
  "bot_response": "Sorry, this order can't be cancelled anymore."
}
```

---

### 9. Wallet Balance

**Endpoint:** `GET /api/bot/wallet/balance/`

**Description:** Get merchant's wallet balance.

**Authentication:** API Key + Merchant Phone

**Example Request:**
```bash
curl -X GET "https://www.orders.axpress.net/api/bot/wallet/balance/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "X-Merchant-Phone: 2348098765432"
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "balance": 20000.0,
    "formatted_balance": "₦20,000"
  },
  "bot_response": "Your wallet balance is ₦20,000."
}
```

---

### 10. Transaction History

**Endpoint:** `GET /api/bot/wallet/transactions/`

**Description:** Get merchant's transaction history.

**Authentication:** API Key + Merchant Phone

**Example Request:**
```bash
curl -X GET "https://www.orders.axpress.net/api/bot/wallet/transactions/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "X-Merchant-Phone: 2348098765432"
```

**Success Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "reference": "order_6158010",
      "type": "debit",
      "type_display": "Debit",
      "amount": "6707.25",
      "formatted_amount": "₦6,707",
      "description": "Order 6158010",
      "status": "completed",
      "created_at": "2026-02-18T20:39:03.730899Z"
    },
    {
      "reference": "TXN-8BEC171FBFD5",
      "type": "credit",
      "type_display": "Credit",
      "amount": "20000.00",
      "formatted_amount": "₦20,000",
      "description": "Test funding for bot testing",
      "status": "completed",
      "created_at": "2026-02-18T20:38:16.780688Z"
    }
  ],
  "bot_response": "You have 2 recent transactions."
}
```

---

## Response Format

All endpoints return JSON responses with the following structure:

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "bot_response": "Human-friendly message in Nigerian English"
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error description",
  "bot_response": "Human-friendly error message"
}
```

---

## Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Invalid API key
- `403 Forbidden` - Merchant not found or access denied
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Order Status Values

- `pending` - Order created, waiting for rider
- `InTransit` - Rider picked up package
- `Delivered` - Package delivered successfully
- `Failed` - Delivery failed
- `Canceled` - Order cancelled

---

## Vehicle Types

- `Bike` - Motorcycle delivery (fastest, cheapest)
- `Car` - Car delivery (medium)
- `Van` - Van delivery (largest capacity, most expensive)

---

## Package Types

- `Box` - Standard box
- `Envelope` - Document envelope
- `Fragile` - Fragile items
- `Food` - Food delivery
- `Document` - Documents
- `Other` - Other items

---

## Phone Number Format

All phone numbers should be in the format: `2348012345678`

- No `+` prefix
- No spaces or dashes
- Must start with `234` (Nigeria country code)

The API will automatically normalize phone numbers with the following prefixes:
- `+234` → `234`
- `0` → `234`

---

## Error Handling

### Invalid API Key
```json
{
  "detail": "Invalid API key"
}
```

### Merchant Not Found
```json
{
  "detail": "Merchant not found for phone: 2348012345678"
}
```

### Insufficient Balance
```json
{
  "success": false,
  "message": "Insufficient wallet balance",
  "bot_response": "Your wallet balance (₦2,000) is not enough for this delivery (₦6,707). Please fund your wallet."
}
```

---

## Integration with respond.io

### Webhook Configuration

1. Set webhook URL to: `https://www.orders.axpress.net/api/bot/`
2. Add header: `X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0`
3. For each request, include `X-Merchant-Phone` header with the WhatsApp user's phone number

### Example Workflow

1. **User sends message on WhatsApp**
2. **respond.io receives message**
3. **respond.io calls bot API** with merchant's phone number
4. **Bot API processes request** and returns `bot_response`
5. **respond.io sends `bot_response`** back to user on WhatsApp

---

## Testing

### Test Credentials

**Test Merchant:**
- Phone: `2348098765432`
- Business: Test Logistics Ltd
- Contact: Chidi Okafor
- Wallet Balance: ₦20,000

### Test Addresses (Lagos, Nigeria)

- Victoria Island, Lagos
- Ikeja City Mall, Lagos
- Lekki Phase 1, Lagos
- Yaba, Lagos
- Surulere, Lagos

---

## Support

For API support or issues, contact:
- Email: support@axpress.net
- Phone: +234 XXX XXX XXXX

---

## Changelog

### Version 1.0.0 (2026-02-18)
- Initial release
- 10 endpoints implemented
- API key authentication
- Phone-based merchant identification
- Google Maps integration for geocoding and routing
- Wallet management
- Order management
- Transaction history

