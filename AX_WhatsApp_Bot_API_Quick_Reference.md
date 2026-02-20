# AX WhatsApp Bot API - Quick Reference

## Production Credentials

**Base URL:** `https://www.orders.axpress.net/api/bot/`

**API Key:** `sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0`

**Headers:**
```
X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0
X-Merchant-Phone: 2348098765432
Content-Type: application/json
```

---

## Endpoints Summary

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 1 | `/lookup/?phone={phone}` | GET | API Key | Lookup merchant by phone |
| 2 | `/signup/` | POST | API Key | Passwordless signup |
| 3 | `/summary/` | GET | API Key + Phone | Dashboard summary |
| 4 | `/orders/get-price/` | POST | API Key + Phone | Calculate delivery price |
| 5 | `/orders/create/` | POST | API Key + Phone | Create order |
| 6 | `/orders/` | GET | API Key + Phone | List orders |
| 7 | `/orders/{order_number}/` | GET | API Key + Phone | Order detail |
| 8 | `/orders/{order_number}/cancel/` | POST | API Key + Phone | Cancel order |
| 9 | `/wallet/balance/` | GET | API Key + Phone | Wallet balance |
| 10 | `/wallet/transactions/` | GET | API Key + Phone | Transaction history |

---

## Quick Examples

### 1. Lookup Merchant
```bash
curl "https://www.orders.axpress.net/api/bot/lookup/?phone=2348012345678" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0"
```

### 2. Signup
```bash
curl -X POST "https://www.orders.axpress.net/api/bot/signup/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "Content-Type: application/json" \
  -d '{"phone":"2348098765432","business_name":"Test Ltd","contact_name":"John"}'
```

### 3. Dashboard Summary
```bash
curl "https://www.orders.axpress.net/api/bot/summary/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "X-Merchant-Phone: 2348098765432"
```

### 4. Get Price Quote
```bash
curl -X POST "https://www.orders.axpress.net/api/bot/orders/get-price/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "X-Merchant-Phone: 2348098765432" \
  -H "Content-Type: application/json" \
  -d '{"pickup_address":"Victoria Island, Lagos","dropoff_address":"Ikeja, Lagos"}'
```

### 5. Create Order
```bash
curl -X POST "https://www.orders.axpress.net/api/bot/orders/create/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "X-Merchant-Phone: 2348098765432" \
  -H "Content-Type: application/json" \
  -d '{
    "pickup_address":"Victoria Island, Lagos",
    "dropoff_address":"Ikeja, Lagos",
    "vehicle_type":"Bike",
    "pickup_contact_name":"John",
    "pickup_contact_phone":"2348098765432",
    "dropoff_contact_name":"Jane",
    "dropoff_contact_phone":"2348087654321",
    "payment_method":"wallet"
  }'
```

### 6. List Orders
```bash
curl "https://www.orders.axpress.net/api/bot/orders/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "X-Merchant-Phone: 2348098765432"
```

### 7. Order Detail
```bash
curl "https://www.orders.axpress.net/api/bot/orders/6158010/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "X-Merchant-Phone: 2348098765432"
```

### 8. Cancel Order
```bash
curl -X POST "https://www.orders.axpress.net/api/bot/orders/6158010/cancel/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "X-Merchant-Phone: 2348098765432"
```

### 9. Wallet Balance
```bash
curl "https://www.orders.axpress.net/api/bot/wallet/balance/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "X-Merchant-Phone: 2348098765432"
```

### 10. Transaction History
```bash
curl "https://www.orders.axpress.net/api/bot/wallet/transactions/" \
  -H "X-API-Key: sk_bot_1wK0I_09ZFhvTtqnb-3SG5Z3GT09rYN8lwX1s_72jr0" \
  -H "X-Merchant-Phone: 2348098765432"
```

---

## Response Structure

All responses include a `bot_response` field with conversational Nigerian English text suitable for WhatsApp.

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "bot_response": "Human-friendly message"
}
```

**Error:**
```json
{
  "success": false,
  "message": "Error description",
  "bot_response": "Human-friendly error message"
}
```

---

## Common Values

**Vehicle Types:** `Bike`, `Car`, `Van`

**Package Types:** `Box`, `Envelope`, `Fragile`, `Food`, `Document`, `Other`

**Order Status:** `pending`, `InTransit`, `Delivered`, `Failed`, `Canceled`

**Phone Format:** `2348012345678` (no + or spaces)

---

## Test Data

**Test Merchant:**
- Phone: `2348098765432`
- Business: Test Logistics Ltd
- Contact: Chidi Okafor

**Test Addresses:**
- Victoria Island, Lagos
- Ikeja City Mall, Lagos
- Lekki Phase 1, Lagos


