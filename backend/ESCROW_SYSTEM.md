# Escrow System Documentation

## Overview

The AX Merchant Portal now uses an **escrow-based payment system** for all wallet-funded orders. This ensures that funds can be easily refunded if orders are canceled or fail, while still being held securely until delivery is completed.

## How It Works

### 1. **Order Placement (Escrow Hold)**

When a merchant places an order using their wallet:

1. ✅ Funds are **held in escrow** (not immediately deducted)
2. ✅ Wallet balance is reduced by the order amount
3. ✅ A `pending` transaction is created with reference `ESCROW-HOLD-{order_number}`
4. ✅ Order is marked with `escrow_held = True`

**Before Escrow:**
```
Wallet Balance: ₦10,000
Order Amount: ₦4,500
→ Wallet immediately debited ₦4,500
→ Hard to refund if order canceled
```

**With Escrow:**
```
Wallet Balance: ₦10,000
Order Amount: ₦4,500
→ Funds held in escrow (wallet shows ₦5,500 available)
→ Easy to refund if order canceled
→ Released when delivery completed
```

### 2. **Delivery Completion (Escrow Release)**

When a delivery is marked as "Done":

1. ✅ Escrow transaction status changed to `completed`
2. ✅ Order marked with `escrow_released = True`
3. ✅ Funds are now permanently deducted (no refund possible)

### 3. **Order Cancellation (Escrow Refund)**

When an order is canceled or fails:

1. ✅ Escrow transaction status changed to `reversed`
2. ✅ Wallet is credited back the escrowed amount
3. ✅ A refund transaction is created with reference `ESCROW-REFUND-{order_number}`
4. ✅ Supports **partial refunds** for multi-drop orders

## API Endpoints

### Release Escrow

**Endpoint:** `POST /api/orders/{order_number}/release-escrow/`

**When to use:** When delivery is completed successfully

**Requirements:**
- Order status must be "Done"
- Escrow must be held (`escrow_held = True`)
- Escrow must not already be released

**Example Request:**
```bash
POST /api/orders/6158001/release-escrow/
Authorization: Bearer {jwt_token}
```

**Example Response:**
```json
{
  "success": true,
  "message": "Escrow released for order #6158001",
  "amount": 4500.00,
  "order_number": "6158001"
}
```

### Refund Escrow

**Endpoint:** `POST /api/orders/{order_number}/refund-escrow/`

**When to use:** When order is canceled or fails

**Requirements:**
- Order status must be "CustomerCanceled", "RiderCanceled", or "Failed"
- Escrow must be held (`escrow_held = True`)

**Example Request (Full Refund):**
```bash
POST /api/orders/6158001/refund-escrow/
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "reason": "Customer canceled order"
}
```

**Example Request (Partial Refund):**
```bash
POST /api/orders/6158002/refund-escrow/
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "reason": "2 out of 5 deliveries failed",
  "partial_amount": 2400.00
}
```

**Example Response:**
```json
{
  "success": true,
  "message": "Escrow refunded for order #6158001",
  "refund_amount": 4500.00,
  "refund_type": "full",
  "order_number": "6158001"
}
```

### Check Escrow Status

**Endpoint:** `GET /api/orders/{order_number}/escrow-status/`

**When to use:** To check current escrow state for an order

**Example Request:**
```bash
GET /api/orders/6158001/escrow-status/
Authorization: Bearer {jwt_token}
```

**Example Response:**
```json
{
  "success": true,
  "order_number": "6158001",
  "order_status": "Pending",
  "escrow_held": true,
  "escrow_released": false,
  "escrow_details": {
    "exists": true,
    "status": "pending",
    "amount": 4500.00,
    "escrow_status": "held",
    "can_refund": true,
    "created_at": "2026-02-15T10:30:00Z",
    "metadata": {
      "escrow_status": "held",
      "can_refund": true,
      "order_number": "6158001"
    }
  }
}
```

## Database Changes

### Order Model

Two new fields added:

```python
escrow_held = models.BooleanField(default=False)
escrow_released = models.BooleanField(default=False)
```

**Migration Required:** Yes, run `python manage.py makemigrations` and `python manage.py migrate`

## Files Modified/Created

1. ✅ **`backend/wallet/escrow.py`** - New escrow manager class
2. ✅ **`backend/orders/models.py`** - Added escrow tracking fields
3. ✅ **`backend/orders/views.py`** - Updated to use escrow instead of direct debit
4. ✅ **`backend/orders/escrow_views.py`** - New escrow management API endpoints
5. ✅ **`backend/orders/urls.py`** - Added escrow routes

## Tracking Completed Escrow Transactions

### How to Identify Completed Escrow

A transaction that went through escrow and was completed has these characteristics:

**1. Order Model:**
```python
order.escrow_held = True      # Funds were held in escrow
order.escrow_released = True  # Funds were released (completed)
order.status = 'Done'         # Delivery completed
```

**2. Transaction Model:**
```python
transaction.reference = 'ESCROW-HOLD-{order_number}'
transaction.status = 'completed'  # Changed from 'pending' to 'completed'
transaction.metadata = {
    'escrow_status': 'released',  # Changed from 'held' to 'released'
    'can_refund': False,          # Changed from True to False
    'order_number': '6158001'
}
```

### API Endpoint: Escrow History

**Endpoint:** `GET /api/orders/escrow-history/`

**Query Parameters:**
- `status` - Filter by transaction status ('pending', 'completed', 'reversed')

**Example: Get All Completed Escrow Transactions**
```bash
GET /api/orders/escrow-history/?status=completed
Authorization: Bearer {jwt_token}
```

**Example Response:**
```json
{
  "success": true,
  "summary": {
    "total_currently_escrowed": 12000.00,
    "total_completed_escrow": 45,
    "total_refunded_escrow": 3,
    "total_completed_amount": 203400.00,
    "total_refunded_amount": 13500.00
  },
  "history": [
    {
      "transaction_id": "uuid-123",
      "order_number": "6158001",
      "order_status": "Done",
      "amount": 4500.00,
      "escrow_status": "released",
      "transaction_status": "completed",
      "can_refund": false,
      "escrow_held": true,
      "escrow_released": true,
      "created_at": "2026-02-15T10:30:00Z",
      "description": "Escrow hold for Quick Send order #6158001",
      "reference": "ESCROW-HOLD-6158001"
    }
  ],
  "count": 45
}
```

### Database Queries

**Get all orders that went through escrow and completed:**
```python
from orders.models import Order

completed_escrow_orders = Order.objects.filter(
    escrow_held=True,
    escrow_released=True,
    status='Done'
)
```

**Get all completed escrow transactions:**
```python
from wallet.models import Transaction

completed_escrow = Transaction.objects.filter(
    reference__startswith='ESCROW-HOLD-',
    status='completed',
    metadata__escrow_status='released'
)
```

**Get escrow history for a specific wallet:**
```python
from wallet.escrow import EscrowManager
from wallet.models import Wallet

wallet = Wallet.objects.get(user=user)

# All completed escrow
completed = EscrowManager.get_completed_escrow_transactions(wallet)

# All refunded escrow
refunded = EscrowManager.get_refunded_escrow_transactions(wallet)

# All escrow (any status)
all_escrow = EscrowManager.get_escrow_history(wallet)
```

## Next Steps

1. **Create Migration:** `python manage.py makemigrations orders`
2. **Run Migration:** `python manage.py migrate`
3. **Test Locally:** Create test orders and verify escrow flow
4. **Deploy to Production:** Update server and run migrations
5. **Update Frontend:** Add escrow status display to order details

