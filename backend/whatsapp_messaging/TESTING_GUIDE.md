# WhatsApp Messaging Integration — Postman Testing Guide

**Base URL:** `http://localhost:8000` (or your server URL)

> Before testing, set `MESSENGER360_API_KEY` in your `.env` file.
> Run: `python manage.py migrate` to create the `WhatsAppMessage` table.

---

## Prerequisites

Make sure these services are running:

```bash
# Terminal 1 — Django
python manage.py runserver 8000

# Terminal 2 — Celery Worker (required — WhatsApp messages are sent via Celery)
celery -A ax_merchant_api worker -l info

# Terminal 3 — Celery Beat (needed for drip campaigns only)
celery -A ax_merchant_api beat -l info
```

---

## ⚡ QUICK TEST — Send a Direct Message (Test-Only Endpoint)

**No authentication required.** This endpoint directly sends a message to test 360Messenger API.

### Check API Configuration

```
GET http://localhost:8000/api/whatsapp/test-info/
```

Response shows if `MESSENGER360_API_KEY` is set and what endpoints are available.

### Send a Test Message

```
POST http://localhost:8000/api/whatsapp/test-send/
Content-Type: application/json
```

```json
{
  "phone_number": "2348012345678",
  "message_text": "Hello! This is a test message from AXpress. Can you receive this?",
  "media_url": ""
}
```

**Response (Success):**
```json
{
  "success": true,
  "message_id": "msg_abc123def456",
  "error": "",
  "is_whatsapp_user": true,
  "details": "✅ Message sent successfully to 2348012345678. Message ID: msg_abc123def456"
}
```

**Response (Failure):**
```json
{
  "success": false,
  "message_id": "",
  "error": "Invalid API Key",
  "is_whatsapp_user": false,
  "details": "❌ Failed to send message to 2348012345678. Error: Invalid API Key"
}
```

### View Message Logs

After sending, check the admin panel:
```
http://localhost:8000/admin/whatsapp_messaging/whatsappmessage/
```

You'll see all sent messages logged with status (sent/failed/pending) and error details.

---

## Step 1 — Seed Vehicles (required for orders)

```
GET http://localhost:8000/api/orders/vehicles/
```

If empty, run this in terminal:

```bash
python manage.py seed_vehicles
```

---

## Step 2 — Create a Merchant (triggers: SIGNUP WhatsApp message)

```
POST http://localhost:8000/api/auth/signup/
Content-Type: application/json
```

```json
{
  "business_name": "Test Merchant Store",
  "contact_name": "John Doe",
  "phone": "2348012345678",
  "email": "testmerchant@example.com",
  "address": "123 Lagos Street, Ikeja",
  "password": "Test@1234",
  "confirm_password": "Test@1234"
}
```

**Expected:** 201 Created + a WhatsApp welcome message sent to `2348012345678`.

**Check Celery logs** — you should see:
```
WhatsApp message sent to 2348012345678, id=...
```

Save the response tokens:
```
access_token → {{merchant_token}}
```

---

## Step 3 — Verify OTP (triggers: ONBOARDING WhatsApp message)

First, find the OTP. Check the signup response or look in the database:

```bash
python manage.py shell -c "from authentication.models import User; u=User.objects.get(phone='2348012345678'); print(u.otp)"
```

Then call:

```
POST http://localhost:8000/api/auth/verify-otp/
Content-Type: application/json
```

```json
{
  "phone": "2348012345678",
  "otp": "123456"
}
```

**Expected:** WhatsApp onboarding message sent to the merchant.

---

## Step 4 — Login as Merchant

```
POST http://localhost:8000/api/auth/login/
Content-Type: application/json
```

```json
{
  "phone": "2348012345678",
  "password": "Test@1234"
}
```

Save from response:
```
access → {{merchant_token}}
```

---

## Step 5 — Create a Dispatcher Account (needed to onboard riders)

```
POST http://localhost:8000/api/auth/signup/
Content-Type: application/json
```

```json
{
  "business_name": "AX Dispatch",
  "contact_name": "Admin Dispatcher",
  "phone": "2348099999999",
  "email": "dispatcher@example.com",
  "address": "AX Office, Lagos",
  "password": "Test@1234",
  "confirm_password": "Test@1234",
  "usertype": "Dispatcher"
}
```

Then set the dispatcher role in the database:

```bash
python manage.py shell -c "
from authentication.models import User
from dispatcher.models import Dispatcher
u = User.objects.get(phone='2348099999999')
u.usertype = 'Dispatcher'
u.save()
Dispatcher.objects.get_or_create(user=u, defaults={'role': 'admin'})
print('Dispatcher created')
"
```

Login as dispatcher:

```
POST http://localhost:8000/api/auth/login/
Content-Type: application/json
```

```json
{
  "phone": "2348099999999",
  "password": "Test@1234"
}
```

Save:
```
access → {{dispatcher_token}}
```

---

## Step 6 — Onboard a Rider (triggers: DISPATCHER_ONBOARDED WhatsApp message)

```
POST http://localhost:8000/api/dispatch/riders/onboarding/
Content-Type: application/json
Authorization: Bearer {{dispatcher_token}}
```

```json
{
  "email": "rider1@example.com",
  "phone": "2348055555555",
  "first_name": "Bayo",
  "last_name": "Rider",
  "password": "Rider@1234",
  "is_verified": true,
  "working_type": "freelancer",
  "team": "Main Team"
}
```

**Expected:** WhatsApp onboarding message sent to `2348055555555`.

Login as rider to get token:

```
POST http://localhost:8000/api/riders/auth/login/
Content-Type: application/json
```

```json
{
  "phone": "2348055555555",
  "password": "Rider@1234"
}
```

Save:
```
access → {{rider_token}}
```

---

## Step 7 — Get Vehicle ID

```
GET http://localhost:8000/api/orders/vehicles/
Authorization: Bearer {{merchant_token}}
```

Save the `id` of the first vehicle (e.g., `1`).

---

## Step 8 — Fund Merchant Wallet (needed for wallet payment)

If you want to test with `payment_method: "wallet"`, fund the wallet first via shell:

```bash
python manage.py shell -c "
from wallet.models import Wallet
from authentication.models import User
u = User.objects.get(phone='2348012345678')
w, _ = Wallet.objects.get_or_create(user=u)
w.balance = 50000
w.save()
print(f'Wallet balance: {w.balance}')
"
```

Or use `"payment_method": "cash_on_pickup"` to skip funding.

---

## Step 9 — Create a Quick Send Order (triggers: ORDER_CREATED WhatsApp message)

```
POST http://localhost:8000/api/orders/quick-send/
Content-Type: application/json
Authorization: Bearer {{merchant_token}}
```

```json
{
  "pickup_address": "12 Allen Avenue, Ikeja, Lagos",
  "sender_name": "John Doe",
  "sender_phone": "2348012345678",
  "dropoff_address": "25 Admiralty Way, Lekki, Lagos",
  "receiver_name": "Jane Smith",
  "receiver_phone": "2348087654321",
  "vehicle": "1",
  "payment_method": "cash_on_pickup",
  "package_type": "Box",
  "distance_km": "15.50",
  "duration_minutes": 45
}
```

**Expected:** WhatsApp message to merchant: "Order #XXXXXXX Created"

Save from response:
```
order_number → {{order_number}}
order_id → {{order_id}}
```

---

## Step 10 — Set Rider on Duty

```
POST http://localhost:8000/api/riders/duty/
Authorization: Bearer {{rider_token}}
```

---

## Step 11 — Check for Order Offers (as rider)

```
GET http://localhost:8000/api/riders/orders/offers/
Authorization: Bearer {{rider_token}}
```

Save the `id` of the offer:
```
offer_id → {{offer_id}}
```

If no offers appear, create one via shell:

```bash
python manage.py shell -c "
from riders.models import OrderOffer
from orders.models import Order
from dispatcher.models import Rider
order = Order.objects.last()
rider = Rider.objects.first()
offer = OrderOffer.objects.create(order=order, rider=rider, status='pending')
print(f'Offer created: {offer.id}')
"
```

---

## Step 12 — Accept Order Offer (triggers: RIDER_ASSIGNED WhatsApp message)

```
POST http://localhost:8000/api/riders/orders/offers/{{offer_id}}/accept/
Authorization: Bearer {{rider_token}}
```

**Expected:** Two WhatsApp messages:
1. To merchant: "Rider Assigned — Order #XXXXXXX"
2. To rider: "New Order Assigned — #XXXXXXX"

---

## Step 13 — Start & Pick Up Order (triggers: ORDER_PICKED_UP WhatsApp message)

Start the order:

```
POST http://localhost:8000/api/orders/start/
Content-Type: application/json
Authorization: Bearer {{rider_token}}
```

```json
{
  "order_number": "{{order_number}}"
}
```

Pick up the order:

```
POST http://localhost:8000/api/orders/pickup/
Content-Type: application/json
Authorization: Bearer {{rider_token}}
```

```json
{
  "order_number": "{{order_number}}"
}
```

**Expected:** WhatsApp message to merchant: "Order #XXXXXXX Picked Up"

---

## Step 14 — Deliver Order (triggers: ORDER_DELIVERED WhatsApp message)

First mark arrived:

```
POST http://localhost:8000/api/orders/arrived/
Content-Type: application/json
Authorization: Bearer {{rider_token}}
```

```json
{
  "order_number": "{{order_number}}"
}
```

Then deliver (use the delivery ID from the order response):

```
POST http://localhost:8000/api/orders/delivery/{{delivery_id}}/deliver/
Content-Type: application/json
Authorization: Bearer {{rider_token}}
```

**Expected:** WhatsApp message to merchant: "Order #XXXXXXX Delivered!"

---

## Step 15 — Cancel an Order (triggers: ORDER_CANCELLED WhatsApp message)

Create another order first (repeat Step 9), then:

```
POST http://localhost:8000/api/orders/cancel/{{new_order_number}}/
Content-Type: application/json
Authorization: Bearer {{merchant_token}}
```

**Expected:** WhatsApp message: "Order #XXXXXXX Cancelled"

---

## Verifying Messages Were Sent

### Option A — Check Django Admin

Go to: `http://localhost:8000/admin/whatsapp_messaging/whatsappmessage/`

You'll see every message with:
- Recipient phone
- Event type
- Status (sent/failed)
- Message content
- 360Messenger message ID

### Option B — Check Celery Worker Logs

Look for lines like:
```
WhatsApp message sent to 2348012345678, id=bcf2b4f0-73f7-...
```

### Option C — Check via 360Messenger Dashboard

Login at `https://app.360messenger.com` and check sent messages.

### Option D — Check via API

```
GET https://api.360messenger.com/v2/message/status?id={{external_message_id}}
Authorization: Bearer {{MESSENGER360_API_KEY}}
```

---

## Summary — WhatsApp Triggers

| Step | Action | WhatsApp Event | Recipient |
|------|--------|---------------|-----------|
| 2 | Merchant signup | `signup` | Merchant |
| 3 | OTP verification | `onboarding` | Merchant |
| 6 | Rider onboarding | `dispatcher_onboarded` | Rider |
| 9 | Create order | `order_created` | Merchant |
| 12 | Accept offer | `rider_assigned` | Merchant + Rider |
| 13 | Pickup order | `order_picked_up` | Merchant |
| 14 | Deliver order | `order_delivered` | Merchant |
| 15 | Cancel order | `order_cancelled` | Merchant |

---

## Environment Variables Needed

Add to your `.env` file:

```
MESSENGER360_API_KEY=your-api-key-from-360messenger-dashboard
```

Get the API key from: `https://app.360messenger.com` → Web Service Information
