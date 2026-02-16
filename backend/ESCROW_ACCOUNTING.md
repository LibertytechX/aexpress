# Escrow System - Clear Accounting Model

## ✅ Problem Solved: Clear Debit/Credit Transactions

### The Issue You Identified
The previous implementation had **one transaction that just changed state**, making it unclear in the transaction history what actually happened to the money.

### The Solution: Proper Double-Entry Accounting

Now every money movement has a **clear debit or credit transaction** with `status='completed'`.

---

## 📊 New Transaction Flow

### 1. Order Placed (Escrow Hold)

**What Happens:**
- Wallet balance **immediately reduced** by order amount
- **DEBIT transaction created** with `status='completed'`
- Transaction marked as escrow via metadata

**Transaction Created:**
```
Reference: ORDER-6158001
Type: debit
Amount: ₦4,500
Status: completed  ← Money actually left the wallet
Balance: ₦10,000 → ₦5,500

Metadata:
{
  "is_escrow": true,
  "escrow_status": "held",
  "can_refund": true,
  "order_number": "6158001"
}
```

**Wallet Balance:**
```
Before: ₦10,000
After:  ₦5,500  ← Money deducted immediately
```

---

### 2. Delivery Completed (Escrow Released)

**What Happens:**
- **No wallet balance change** (money already deducted)
- **No new transaction created**
- Original transaction metadata updated to mark as "released"

**Transaction Updated:**
```
Reference: ORDER-6158001
Type: debit
Amount: ₦4,500
Status: completed  ← Still completed (no change)
Balance: ₦10,000 → ₦5,500

Metadata:
{
  "is_escrow": true,
  "escrow_status": "released",  ← Changed from "held"
  "can_refund": false,          ← Changed from true
  "order_number": "6158001",
  "released_at": "2026-02-16T10:30:00Z"
}
```

**Wallet Balance:**
```
Before: ₦5,500
After:  ₦5,500  ← No change (money already gone)
```

---

### 3. Order Canceled (Escrow Refunded)

**What Happens:**
- Wallet balance **increased** by refund amount
- **CREDIT transaction created** with `status='completed'`
- Original debit transaction metadata updated

**New Transaction Created:**
```
Reference: REFUND-6158001
Type: credit  ← CREDIT (money returns)
Amount: ₦4,500
Status: completed  ← Money actually returned to wallet
Balance: ₦5,500 → ₦10,000

Metadata:
{
  "is_escrow_refund": true,
  "escrow_status": "refunded",
  "order_number": "6158001",
  "original_order_ref": "ORDER-6158001",
  "refund_type": "full"
}
```

**Original Transaction Updated:**
```
Reference: ORDER-6158001
Type: debit
Amount: ₦4,500
Status: completed  ← Still completed (no change)
Balance: ₦10,000 → ₦5,500

Metadata:
{
  "is_escrow": true,
  "escrow_status": "refunded",  ← Changed from "held"
  "can_refund": false,          ← Changed from true
  "order_number": "6158001",
  "refunded_at": "2026-02-16T11:00:00Z"
}
```

**Wallet Balance:**
```
Before: ₦5,500
After:  ₦10,000  ← Money returned!
```

---

## 📋 Transaction History View

### Example: Order Placed → Canceled → Refunded

**Transaction History (Newest First):**

```
┌─────────────────────────────────────────────────────────────┐
│ REFUND-6158001                             [NEWEST]         │
│ Type: CREDIT                                                │
│ Amount: +₦4,500                                             │
│ Status: completed                                           │
│ Description: Refund for canceled order #6158001            │
│ Balance: ₦5,500 → ₦10,000                                   │
│ Date: 2026-02-16 11:00:00                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ORDER-6158001                                               │
│ Type: DEBIT                                                 │
│ Amount: -₦4,500                                             │
│ Status: completed                                           │
│ Description: Payment for order #6158001 (held in escrow)   │
│ Balance: ₦10,000 → ₦5,500                                   │
│ Date: 2026-02-16 10:00:00                                   │
│ Metadata: escrow_status = "refunded"                        │
└─────────────────────────────────────────────────────────────┘
```

**Clear Accounting:**
- ✅ Debit: -₦4,500 (money left wallet)
- ✅ Credit: +₦4,500 (money returned to wallet)
- ✅ Net Effect: ₦0 (order was canceled, no charge)

---

### Example: Order Placed → Completed → Released

**Transaction History:**

```
┌─────────────────────────────────────────────────────────────┐
│ ORDER-6158001                                               │
│ Type: DEBIT                                                 │
│ Amount: -₦4,500                                             │
│ Status: completed                                           │
│ Description: Payment for order #6158001 (held in escrow)   │
│ Balance: ₦10,000 → ₦5,500                                   │
│ Date: 2026-02-16 10:00:00                                   │
│ Metadata: escrow_status = "released"                        │
└─────────────────────────────────────────────────────────────┘
```

**Clear Accounting:**
- ✅ Debit: -₦4,500 (money left wallet)
- ✅ No credit (delivery completed, platform keeps money)
- ✅ Net Effect: -₦4,500 (order completed, charged)

---

## 🎯 Key Benefits

### 1. Clear Transaction History
Every debit and credit is a separate, completed transaction

### 2. Accurate Wallet Balance
Wallet balance always reflects actual available money

### 3. Easy Reconciliation
Sum of all debits - sum of all credits = current balance

### 4. Audit Trail
Can track exactly when money moved and why

### 5. Standard Accounting
Follows double-entry bookkeeping principles

---

## 📊 Comparison: Old vs New

| Aspect | Old (State Changes) | New (Clear Transactions) |
|--------|-------------------|-------------------------|
| **Order Placed** | 1 transaction (pending) | 1 DEBIT (completed) |
| **Order Completed** | Update status to completed | Update metadata only |
| **Order Canceled** | Update status + 1 CREDIT | Keep original + 1 CREDIT |
| **Transaction Count** | 1-2 transactions | 1-2 transactions |
| **Clarity** | ❌ Status changes confusing | ✅ Clear debit/credit |
| **Wallet Balance** | ✅ Accurate | ✅ Accurate |
| **Accounting** | ❌ Non-standard | ✅ Standard double-entry |

---

## 🔍 How to Query

### Get All Escrow Debits
```python
escrow_debits = Transaction.objects.filter(
    wallet=wallet,
    type='debit',
    metadata__is_escrow=True
)
```

### Get All Escrow Refunds
```python
escrow_refunds = Transaction.objects.filter(
    wallet=wallet,
    type='credit',
    metadata__is_escrow_refund=True
)
```

### Calculate Net Escrow Impact
```python
debits = escrow_debits.aggregate(total=Sum('amount'))['total'] or 0
credits = escrow_refunds.aggregate(total=Sum('amount'))['total'] or 0
net_escrow_cost = debits - credits
```

