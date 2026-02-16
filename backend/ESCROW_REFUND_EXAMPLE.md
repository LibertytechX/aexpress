# Escrow Refund Examples

## Example 1: Full Refund (Order Canceled)

### Initial State
```
Wallet Balance: ₦10,000
Order #6158001: Quick Send, ₦4,500
```

### After Order Placed (Escrow Hold)
```
Wallet Balance: ₦5,500
Available: ₦5,500
Escrowed: ₦4,500

Transaction History:
┌─────────────────────────────────────────────────────────────┐
│ ESCROW-HOLD-6158001                                         │
│ Type: Debit                                                 │
│ Amount: -₦4,500                                             │
│ Status: pending                                             │
│ Description: Escrow hold for Quick Send order #6158001     │
│ Balance: ₦10,000 → ₦5,500                                   │
└─────────────────────────────────────────────────────────────┘
```

### Customer Cancels Order
```
Order Status: CustomerCanceled
```

### After Refund
```
Wallet Balance: ₦10,000  ← Money returned!
Available: ₦10,000
Escrowed: ₦0

Transaction History:
┌─────────────────────────────────────────────────────────────┐
│ ESCROW-REFUND-6158001                          [NEWEST]     │
│ Type: Credit                                                │
│ Amount: +₦4,500                                             │
│ Status: completed                                           │
│ Description: Refund for canceled order #6158001            │
│ Balance: ₦5,500 → ₦10,000                                   │
│ Metadata: {                                                 │
│   "escrow_status": "refunded",                              │
│   "refund_type": "full",                                    │
│   "original_escrow_ref": "ESCROW-HOLD-6158001"              │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ESCROW-HOLD-6158001                                         │
│ Type: Debit                                                 │
│ Amount: -₦4,500                                             │
│ Status: reversed  ← Changed from "pending"                  │
│ Description: Escrow hold for Quick Send order #6158001     │
│ Balance: ₦10,000 → ₦5,500                                   │
│ Metadata: {                                                 │
│   "escrow_status": "refunded",  ← Changed from "held"       │
│   "can_refund": false           ← Changed from true         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Example 2: Partial Refund (Multi-Drop, Some Failed)

### Initial State
```
Wallet Balance: ₦10,000
Order #6158002: Multi-Drop, 5 deliveries × ₦1,200 = ₦6,000
```

### After Order Placed
```
Wallet Balance: ₦4,000
Escrowed: ₦6,000
```

### 3 Deliveries Completed, 2 Failed
```
Completed: 3 deliveries (₦3,600)
Failed: 2 deliveries (₦2,400)
```

### Partial Refund Request
```bash
POST /api/orders/6158002/refund-escrow/
{
  "reason": "2 out of 5 deliveries failed",
  "partial_amount": 2400.00
}
```

### After Partial Refund
```
Wallet Balance: ₦6,400  ← Partial refund received
Available: ₦6,400
Escrowed: ₦3,600  ← Remaining escrow for completed deliveries

Transaction History:
┌─────────────────────────────────────────────────────────────┐
│ ESCROW-REFUND-6158002                          [NEWEST]     │
│ Type: Credit                                                │
│ Amount: +₦2,400                                             │
│ Status: completed                                           │
│ Description: 2 out of 5 deliveries failed                  │
│ Balance: ₦4,000 → ₦6,400                                    │
│ Metadata: {                                                 │
│   "escrow_status": "refunded",                              │
│   "refund_type": "partial",                                 │
│   "original_escrow_ref": "ESCROW-HOLD-6158002"              │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ESCROW-HOLD-6158002                                         │
│ Type: Debit                                                 │
│ Amount: -₦6,000                                             │
│ Status: pending  ← Still pending (not reversed)             │
│ Description: Escrow hold for Multi-Drop order #6158002     │
│ Balance: ₦10,000 → ₦4,000                                   │
│ Metadata: {                                                 │
│   "escrow_status": "held",                                  │
│   "partial_refund": 2400.00,  ← Tracks partial refund      │
│   "remaining_escrow": 3600.00, ← Remaining amount           │
│   "can_refund": true           ← Can still refund more      │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
```

### Later: Release Remaining Escrow
```bash
POST /api/orders/6158002/release-escrow/
```

### After Release
```
Wallet Balance: ₦6,400  ← No change (already deducted)
Escrowed: ₦0

Transaction History shows:
- ESCROW-HOLD-6158002: status = "completed", escrow_status = "released"
- ESCROW-REFUND-6158002: Still shows partial refund of ₦2,400
```

---

## Summary: What Happens on Reverse

### Full Refund
1. ✅ Wallet credited with full escrow amount
2. ✅ Escrow transaction status → `reversed`
3. ✅ Escrow metadata → `escrow_status: "refunded"`
4. ✅ New refund transaction created (type: `credit`)
5. ✅ Order remains `escrow_held=True, escrow_released=False`

### Partial Refund
1. ✅ Wallet credited with partial amount
2. ✅ Escrow transaction status → `pending` (still active)
3. ✅ Escrow metadata → tracks partial refund and remaining amount
4. ✅ New refund transaction created (type: `credit`)
5. ✅ Can still release or refund remaining escrow

### Key Differences from Release
| Action | Release (Completed) | Refund (Canceled) |
|--------|-------------------|-------------------|
| Wallet Balance | No change (already deducted) | Credited back |
| Escrow Status | `completed` | `reversed` |
| Escrow Metadata | `released` | `refunded` |
| New Transaction | Optional | Yes (ESCROW-REFUND) |
| Transaction Type | N/A | `credit` |
| Money Flow | Platform keeps money | Merchant gets money back |

