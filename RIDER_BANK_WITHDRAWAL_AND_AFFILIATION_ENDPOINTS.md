# AXpress API Documentation — Rider Bank Withdrawals & Affiliation System

This document outlines the API endpoints implemented for:
1. **Independent Rider Bank Directory, Account Enquiry & Wema CoreBanking Payouts**
2. **Public Affiliation Code Verification**
3. **Merchant & Rider Affiliation Management**
4. **Dispatcher Affiliated Fleet & Commission Tracking**

---

## 1. Rider Bank Payout & Account Verification Endpoints

### 1.1 List Supported Nigerian Banks
Retrieves the cached list of supported commercial banks, microfinance banks, and fintech institutions in Nigeria.

- **URL:** `GET /api/riders/banks/`
- **Authentication:** `None` (Public / `AllowAny`)
- **Headers:** `Content-Type: application/json`

#### Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Banks retrieved successfully.",
  "data": [
    {
      "id": "18f50682-1234-4567-89ab-cdef01234567",
      "name": "Access Bank",
      "bank_code": "044",
      "cbn_code": "000014",
      "ussd_short_code": "*901#",
      "bank_short_name": "Access"
    },
    {
      "id": "42c38501-1234-4567-89ab-cdef01234567",
      "name": "Guaranty Trust Bank",
      "bank_code": "058",
      "cbn_code": "000013",
      "ussd_short_code": "*737#",
      "bank_short_name": "GTBank"
    },
    {
      "id": "a93bc710-1234-4567-89ab-cdef01234567",
      "name": "Wema Bank",
      "bank_code": "035",
      "cbn_code": "000017",
      "ussd_short_code": "*945#",
      "bank_short_name": "Wema"
    }
  ],
  "status_code": 200
}
```

---

### 1.2 Bank Account Name Enquiry
Verifies an external bank account number and bank code via LibertyPay Account Enquiry before withdrawal.

- **URL:** `POST /api/riders/wallet/verify-account/`
- **Authentication:** `None` (Public / `AllowAny`)
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "account_number": "0123456789",
  "bank_code": "058"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `account_number` | `string` | **Yes** | Exactly 10-digit NUBAN account number. |
| `bank_code` | `string` | **Yes** | 3-digit bank code or 6-digit CBN/NIBSS institution code. |

#### Success Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Account verified successfully.",
  "data": {
    "account_name": "JOHN DOE",
    "account_number": "0123456789",
    "bank_code": "000013",
    "currency_code": "NGN"
  },
  "status_code": 200
}
```

#### Error Response (`400 Bad Request`)
```json
{
  "status": "error",
  "message": "Account verification failed. Please check the account number and bank code.",
  "data": {},
  "status_code": 400
}
```

---

### 1.3 Withdraw Wallet Earnings to Bank Account
Allows independent riders to withdraw funds from their wallet to an external bank account via Wema CoreBanking. Enforces double-entry ledger deduction, pending Cash on Delivery (COD) netting, and instant automatic refund upon external transfer rejection.

- **URL:** `POST /api/riders/wallet/withdraw/`
- **Authentication:** `Bearer <Rider JWT>` (`IsAuthenticated`, `IsRider`)
- **Headers:** `Authorization: Bearer <token>`, `Content-Type: application/json`

#### Request Body
```json
{
  "amount": 25000.00,
  "account_number": "0123456789",
  "account_name": "JOHN DOE",
  "bank_code": "058",
  "bank_name": "Guaranty Trust Bank",
  "narration": "Weekly earnings payout",
  "pin": "1234"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `amount` | `decimal` | **Yes** | Amount to withdraw. Minimum is `₦100.00`. |
| `account_number` | `string` | **Yes** | Verified 10-digit NUBAN account number. |
| `account_name` | `string` | **Yes** | Account name verified via account enquiry. |
| `bank_code` | `string` | **Yes** | Destination bank code or CBN institution code. |
| `pin` | `string` | **Yes** | 4-digit transaction PIN configured by the rider. |
| `bank_name` | `string` | No | Optional human-readable bank name. |
| `narration` | `string` | No | Remark for the transfer (default: `"Earnings withdrawal by <rider_id>"`). |
| `is_sandbox` | `boolean` | No | Optional sandbox simulation flag (bypasses external CoreBanking). |
| `mode` | `string` | No | `"SANDBOX"` or `"LIVE"`. |

#### Success Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Withdrawal request processed successfully.",
  "data": {
    "reference": "WDR-A93BC7101234",
    "amount": 25000.0,
    "account_number": "0123456789",
    "account_name": "JOHN DOE",
    "bank_code": "058",
    "status": "success",
    "remaining_balance": 15420.50
  },
  "status_code": 200
}
```

#### Error Responses
- **Missing or Invalid Transaction PIN:**
  ```json
  {
    "status": "error",
    "message": "Transaction PIN is required.",
    "data": {},
    "status_code": 400
  }
  ```
  ```json
  {
    "status": "error",
    "message": "Invalid transaction PIN. Please enter the correct PIN.",
    "data": {},
    "status_code": 400
  }
  ```
- **Transaction PIN Not Configured:**
  ```json
  {
    "status": "error",
    "message": "Transaction PIN has not been set. Please set your transaction PIN before withdrawing.",
    "data": {},
    "status_code": 400
  }
  ```
- **Insufficient Withdrawable Balance (Pending COD restriction):**
  ```json
  {
    "status": "error",
    "message": "Insufficient withdrawable balance. Withdrawable: ₦12,500.00 (Pending unremitted COD: ₦15,000.00)",
    "data": {},
    "status_code": 400
  }
  ```
- **Company Fleet Rider Restricted:**
  ```json
  {
    "status": "error",
    "message": "Only independent riders are permitted to withdraw wallet earnings.",
    "data": {},
    "status_code": 403
  }
  ```
- **CoreBanking Transfer Rejected (Refunded):**
  ```json
  {
    "status": "error",
    "message": "Destination bank unavailable. Your wallet balance has been refunded.",
    "data": {},
    "status_code": 422
  }
  ```

---

### 1.4 Set or Change Transaction PIN
Allows riders to configure a new 4-digit transaction PIN, or update an existing PIN by validating their current PIN or account password.

- **URL:** `POST /api/riders/wallet/pin/` (alias: `POST /api/riders/wallet/set-pin/`)
- **Authentication:** `Bearer <Rider JWT>` (`IsAuthenticated`, `IsRider`)
- **Headers:** `Authorization: Bearer <token>`, `Content-Type: application/json`

#### Initial Setup Request (when no PIN exists yet)
```json
{
  "pin": "1234",
  "confirm_pin": "1234"
}
```

#### Change PIN Request (when PIN is already set)
```json
{
  "old_pin": "1234",
  "pin": "5678",
  "confirm_pin": "5678"
}
```
*Note: If `old_pin` is forgotten, pass `"password": "your_account_password"` instead.*

| Field | Type | Required | Description |
|---|---|---|---|
| `pin` | `string` | **Yes** | Exactly 4 numeric digits. |
| `confirm_pin` | `string` | **Yes** | Must match `pin`. |
| `old_pin` | `string` | Conditional | Current 4-digit PIN (required if updating existing PIN). |
| `password` | `string` | Conditional | Account login password (alternative to `old_pin`). |

#### Success Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Transaction PIN set successfully.",
  "data": {
    "has_transaction_pin": true
  },
  "status_code": 200
}
```

---

### 1.5 Check Transaction PIN Status
Checks if the authenticated rider has configured a transaction PIN.

- **URL:** `GET /api/riders/wallet/pin/`
- **Authentication:** `Bearer <Rider JWT>` (`IsAuthenticated`, `IsRider`)
- **Headers:** `Authorization: Bearer <token>`

#### Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Transaction PIN status retrieved successfully.",
  "data": {
    "has_transaction_pin": true
  },
  "status_code": 200
}
```

---

### 1.6 Verify Transaction PIN
Verifies a rider's 4-digit transaction PIN without triggering a withdrawal.

- **URL:** `POST /api/riders/wallet/pin/verify/`
- **Authentication:** `Bearer <Rider JWT>` (`IsAuthenticated`, `IsRider`)
- **Headers:** `Authorization: Bearer <token>`, `Content-Type: application/json`

#### Request Body
```json
{
  "pin": "1234"
}
```

#### Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Transaction PIN verified successfully.",
  "data": {
    "valid": true
  },
  "status_code": 200
}
```

---

## 2. Public Affiliation Code Verification Endpoints

Validates dispatcher affiliation codes in real-time during onboarding or profile editing without requiring login.

- **Available URLs:**
  - `GET/POST /api/auth/affiliation/verify/`
  - `GET/POST /api/merchant/affiliation/verify/`
  - `GET/POST /api/riders/affiliation/verify/`
  - `GET/POST /api/affiliation/verify/`
- **Authentication:** `None` (Public / `AllowAny`)

### 2.1 GET Verification
```http
GET /api/auth/affiliation/verify/?code=HUB001
```
*(Accepts query param `code` or `affiliation_code`, case-insensitive, with whitespace trimming).*

### 2.2 POST Verification
```http
POST /api/auth/affiliation/verify/
Content-Type: application/json

{
  "affiliation_code": "HUB001"
}
```
*(Accepts either `{"affiliation_code": "..."}` or `{"code": "..."}`).*

#### Success Response (`200 OK`)
```json
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
```

#### Error Response (`400 Bad Request`)
- **Missing Code:** `"Affiliation code is required."`
- **Unknown Code:** `"Invalid affiliation code. No active dispatcher found with this code."`
- **Non-Affiliate (Admin):** `"This affiliation code does not belong to an active Hub Captain or Zone Lead."`
- **Inactive Account:** `"This affiliation code belongs to an inactive account."`

---

## 3. Merchant Affiliation Endpoints

### 3.1 Get Merchant Affiliation Status
Retrieves current affiliation status and linked dispatcher details for the authenticated merchant profile.

- **URL:** `GET /api/auth/merchant/affiliation/` *(or `/api/merchant/affiliation/`)*
- **Authentication:** `Bearer <Merchant JWT>`

#### Response (`200 OK`)
```json
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

---

### 3.2 Affiliate Merchant to Dispatcher
Links an existing merchant account to a Hub Captain or Zone Lead dispatcher using their affiliation code. *(Note: New merchants can also pass `affiliation_code` directly in `POST /api/auth/signup/`).*

- **URL:** `POST /api/auth/merchant/affiliation/` *(or `/api/merchant/affiliation/`)*
- **Authentication:** `Bearer <Merchant JWT>`

#### Request Body
```json
{
  "affiliation_code": "HUB001"
}
```

#### Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Successfully affiliated with dispatcher Ikeja Hub Logistics",
  "data": {
    "is_affiliated": true,
    "affiliated_at": "2026-10-15T14:20:00Z",
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

---

## 4. Rider Affiliation Endpoints

### 4.1 Get / Set Rider Affiliation
Retrieves status or links an independent rider profile to a dispatcher.

- **URL:** `GET /api/riders/affiliation/` and `POST /api/riders/affiliation/`
- **Authentication:** `Bearer <Rider JWT>`

#### POST Request Body
```json
{
  "affiliation_code": "HUB001"
}
```

#### Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Successfully affiliated with dispatcher",
  "data": {
    "is_affiliated": true,
    "affiliated_at": "2026-10-14T10:15:00Z",
    "dispatcher": {
      "id": "d44bd075-412f-4d37-8dc0-7df81320ddcd",
      "name": "Alice Hub Captain",
      "role": "hub_captain",
      "role_display": "Hub Captain",
      "affiliation_code": "HUB001"
    }
  },
  "status_code": 200
}
```

---

## 5. Dispatcher Fleet Affiliation & Commission Endpoints

### 5.1 List Affiliated Merchants
Paginated list of merchants linked to the authenticated Hub Captain or Zone Lead dispatcher.

- **URL:** `GET /api/dispatch/affiliation/merchants/`
- **Authentication:** `Bearer <Dispatcher JWT>`
- **Query Parameters:**
  - `page` *(optional, int)*: Page number (default: `1`).
  - `page_size` *(optional, int)*: Items per page (default: `20`).
  - `search` *(optional, str)*: Search by business name, merchant ID, phone, or email.

#### Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Affiliated merchants retrieved successfully",
  "data": {
    "count": 42,
    "results": [
      {
        "id": "97e68fa2-1234-4567-89ab-cdef01234567",
        "merchant_id": "261603",
        "business_name": "Acme Retail Ltd",
        "contact_name": "Jane Doe",
        "phone": "+2348055554444",
        "email": "jane@acmeretail.ng",
        "status": "active",
        "is_active": true,
        "is_approved": true,
        "merchant_type": "Retail Store",
        "affiliated_at": "2026-10-15T09:30:00Z",
        "total_orders_completed": 156,
        "monthly_orders_completed": 34,
        "monthly_commission_earned": 102000.0
      }
    ]
  },
  "status_code": 200
}
```

---

### 5.2 Dispatcher Affiliation Summary
High-level affiliation metrics for the dispatcher portal dashboard.

- **URL:** `GET /api/dispatch/affiliation/summary/`
- **Authentication:** `Bearer <Dispatcher JWT>`

#### Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Affiliation summary retrieved successfully",
  "data": {
    "affiliation_code": "HUB001",
    "total_affiliated_riders": 28,
    "affiliated_riders_count": 28,
    "active_riders_this_month": 19,
    "total_affiliated_merchants": 14,
    "affiliated_merchants_count": 14,
    "active_merchants_this_month": 11,
    "current_month": "2026-10",
    "monthly_commission": 150000.0,
    "previous_month_commission": 210000.0,
    "total_commission_earned": 840000.0,
    "commission_rate_per_order": 3000.0
  },
  "status_code": 200
}
```

---

### 5.3 Dispatcher Affiliation Commission Ledger
Detailed ledger entries of ₦3,000 affiliation payouts earned from rider and merchant order completions, with audit trails and same-dispatcher deduplication.

- **URL:** `GET /api/dispatch/affiliation/commissions/`
- **Authentication:** `Bearer <Dispatcher JWT>`
- **Query Parameters:**
  - `page` *(optional, int)*: Page number.
  - `page_size` *(optional, int)*: Items per page.
  - `month` *(optional, str)*: Filter by month format `YYYY-MM` (e.g. `2026-10`).
  - `source` *(optional, str)*: Filter by affiliation source (`rider` or `merchant`).
  - `rider_id` *(optional, str)*: Filter by rider UUID.
  - `merchant_id` *(optional, str)*: Filter by merchant numerical ID.

#### Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Commissions retrieved successfully",
  "data": {
    "count": 1,
    "results": [
      {
        "id": "b968fc24-1234-4567-89ab-cdef01234567",
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
