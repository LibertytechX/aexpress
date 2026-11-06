# AXpress Backend Audit for OCC Integration

> **Date:** 2026-03-08
> **Purpose:** Identify existing endpoints, gaps, and build requirements for the Operations Command Center (OCC) dashboard to consume data from this main Assured Express backend.

---

## Table of Contents

1. [Existing Endpoints](#1-existing-endpoints)
2. [Endpoint-to-OCC Mapping](#2-endpoint-to-occ-data-mapping)
3. [Identified Gaps](#3-identified-gaps)
4. [Endpoints to Build](#4-endpoints-to-build)
5. [DB Schema Gaps](#5-db-schema-gaps--models--fields-to-add)
6. [Inter-Project Auth Proposal](#6-inter-project-auth-proposal)
7. [Summary](#7-summary)

---

## 1. Existing Endpoints

### 1.1 Authentication (`/api/auth/`)

| URL | Method | View | Description |
|-----|--------|------|-------------|
| `signup/` | POST | SignupView | User registration |
| `login/` | POST | LoginView | User login |
| `logout/` | POST | LogoutView | User logout |
| `refresh/` | POST | TokenRefreshView | JWT token refresh |
| `verify-email/` | POST | VerifyEmailView | Verify user email |
| `verify-otp/` | POST | VerifyOTPView | Verify OTP |
| `resend-otp/` | POST | ResendOTPView | Resend OTP code |
| `resend-verification/` | POST | ResendVerificationEmailView | Resend verification email |
| `request-password-reset/` | POST | RequestPasswordResetView | Request password reset |
| `reset-password/` | POST | ResetPasswordView | Reset password with token |
| `mobile/request-password-reset/` | POST | MobileRequestPasswordResetView | Mobile password reset request |
| `mobile/reset-password/` | POST | MobileResetPasswordView | Mobile password reset |
| `me/` | GET, PUT | UserProfileView | Get/update current user profile |
| `profile/` | GET, PUT | UserProfileView | Profile alias |
| `addresses/` | GET, POST | AddressListCreateView | List/create addresses |
| `addresses/<uuid>/` | GET, PUT, DELETE | AddressDetailView | Address CRUD |
| `addresses/<uuid>/set-default/` | POST | SetDefaultAddressView | Set default address |

### 1.2 Orders (`/api/orders/`)

| URL | Method | View | Description |
|-----|--------|------|-------------|
| `vehicles/` | GET | VehicleListView | List available vehicles |
| `vehicles/<int:id>/` | PATCH | VehicleUpdateView | Update vehicle details |
| `quick-send/` | POST | QuickSendView | Create a quick-send order |
| `multi-drop/` | POST | MultiDropView | Create multi-drop order |
| `bulk-import/` | POST | BulkImportView | Bulk import orders from CSV |
| `calculate-fare/` | POST | CalculateFareView | Calculate delivery fare |
| `bulk-calculate-fare/` | POST | BulkCalculateFareView | Calculate fares in bulk |
| _(root)_ | GET | OrderListView | List orders |
| `<order_number>/` | GET | OrderDetailView | Get order details |
| `assigned/` | GET | AssignedOrdersView | List assigned orders |
| `assigned/<order_number>/` | GET | AssignedOrderDetailView | Assigned order detail |
| `assigned-routes/` | GET | AssignedRoutesView | Assigned delivery routes |
| `pickup/` | POST | OrderPickupView | Mark order picked up |
| `start/` | POST | OrderStartView | Start delivery |
| `arrived/` | POST | OrderArrivedView | Rider arrived at dropoff |
| `status/` | POST | OrderStatusChangeView | Change order status |
| `delivery/<uuid>/start/` | POST | DeliveryStartView | Start delivery leg |
| `delivery/<uuid>/deliver/` | POST | DeliveryCompleteView | Complete delivery leg |
| `stats/` | GET | OrderStatsView | Order statistics (merchant-scoped) |
| `escrow-history/` | GET | EscrowHistoryView | Escrow transaction history |
| `cancelable/` | GET | CancelableOrdersView | List cancelable orders |
| `release-escrow/<order_number>/` | POST | ReleaseEscrowView | Release escrowed funds |
| `refund-escrow/<order_number>/` | POST | RefundEscrowView | Refund escrowed funds |
| `escrow-status/<order_number>/` | GET | EscrowStatusView | Check escrow status |
| `cancel/<order_number>/` | POST | CancelOrderView | Cancel order |
| `<uuid>/rider-cancel/` | POST | cancel_order | Rider cancels order |

### 1.3 Riders (`/api/riders/`)

| URL | Method | View | Description |
|-----|--------|------|-------------|
| `auth/login/` | POST | RiderLoginView | Rider login |
| `auth/refresh/` | POST | RiderTokenRefreshView | Refresh rider JWT |
| `auth/me/` | GET | RiderMeView | Current rider profile |
| `device/` | POST | RiderDeviceRegistrationView | Register device |
| `device/permissions/` | POST | RiderUpdatePermissionsView | Update device permissions |
| `orders/history/` | GET | RiderOrderHistoryView | Rider order history |
| `orders/offers/` | GET | OrderOfferListView | Available order offers |
| `orders/offers/<uuid>/accept/` | POST | OrderOfferAcceptView | Accept order offer |
| `orders/<order_id>/` | GET | RiderOrderDetailView | Order details |
| `orders-today/` | GET | RiderTodayTripsView | Today's trips |
| `duty/` | POST | RiderToggleDutyView | Toggle online/offline |
| `location/update/` | POST | RiderLocationUpdateView | Update GPS location |
| `area-demand/` | GET | AreaDemandListView | Area demand info |
| `earnings/` | GET | RiderEarningsView | Rider earnings (today/week/month) |
| `wallet/info/` | GET | RiderWalletInfoView | Wallet information |
| `wallet/transactions/` | GET | RiderTransactionListView | Wallet transactions |
| `notifications/` | GET | RiderNotificationListView | List notifications |
| `notifications/<uuid>/` | GET | RiderNotificationDetailView | Notification detail |
| `notifications/<uuid>/read/` | POST | RiderNotificationMarkReadView | Mark notification read |
| `ride-to-own/` | GET | RideToOwnView | Ride-to-own program info |
| `monthly-target/` | GET | MonthlyTargetView | Monthly targets |
| `challenges/` | GET | ChallengeListView | Gamification challenges |
| `leaderboard/` | GET | LeaderboardView | Leaderboard |
| `dashboard-summary/` | GET | DashboardSummaryView | Dashboard summary |

### 1.4 Referrals (`/api/riders/referrals/`)

| URL | Method | View | Description |
|-----|--------|------|-------------|
| `overview/` | GET | ReferralOverviewView | Referral program overview |
| `businesses/` | GET | ReferralBusinessListView | Referral businesses |
| `register-business/` | POST | RegisterReferralBusinessView | Register referral business |

### 1.5 Dispatcher (`/api/dispatch/`)

#### Riders Resource (ViewSet — full CRUD)

| URL | Method | Description |
|-----|--------|-------------|
| `riders/` | GET | List all riders |
| `riders/` | POST | Create rider |
| `riders/<id>/` | GET, PUT, PATCH, DELETE | Rider CRUD |
| `riders/<id>/reset_password/` | POST | Reset rider password |
| `riders/<id>/assign_vehicle/` | POST | Assign vehicle to rider |
| `riders/<id>/toggle_duty/` | POST | Toggle duty status |
| `riders/<id>/update_location/` | PATCH | Update rider location |

#### Orders Resource (ViewSet — full CRUD)

| URL | Method | Description |
|-----|--------|-------------|
| `orders/` | GET | List all orders |
| `orders/` | POST | Create order |
| `orders/<order_number>/` | GET, PUT, PATCH, DELETE | Order CRUD |
| `orders/<order_number>/assign_rider/` | POST | Assign rider to order |
| `orders/<order_number>/update_status/` | POST | Update order status |
| `orders/<order_number>/update-price/` | PATCH | Update delivery fee |
| `orders/<order_number>/generate-relay-route/` | POST | Generate relay route |

#### Merchants Resource (ViewSet — full CRUD)

| URL | Method | Description |
|-----|--------|-------------|
| `merchants/` | GET, POST | List/create merchants |
| `merchants/<id>/` | GET, PUT, PATCH, DELETE | Merchant CRUD |

#### Merchant Pricing Overrides (ViewSet — full CRUD)

| URL | Method | Description |
|-----|--------|-------------|
| `merchant-pricing-overrides/` | GET, POST | List/create overrides |
| `merchant-pricing-overrides/<id>/` | GET, PUT, PATCH, DELETE | Override CRUD |

#### Zones Resource (ViewSet — full CRUD)

| URL | Method | Description |
|-----|--------|-------------|
| `zones/` | GET, POST | List/create zones |
| `zones/<id>/` | GET, PUT, PATCH, DELETE | Zone CRUD |

#### Relay Nodes Resource (ViewSet — full CRUD)

| URL | Method | Description |
|-----|--------|-------------|
| `relay-nodes/` | GET, POST | List/create relay nodes |
| `relay-nodes/<id>/` | GET, PUT, PATCH, DELETE | Relay node CRUD |

#### Dispatchers Resource

| URL | Method | Description |
|-----|--------|-------------|
| `dispatchers/` | GET, POST | List/create dispatchers |

#### Vehicle Assets Resource (ViewSet — full CRUD)

| URL | Method | Description |
|-----|--------|-------------|
| `vehicle-assets/` | GET, POST | List/create vehicle assets |
| `vehicle-assets/<id>/` | GET, PUT, PATCH, DELETE | Vehicle asset CRUD |

#### Standalone Dispatcher Endpoints

| URL | Method | Description |
|-----|--------|-------------|
| `settings/` | GET, POST | System settings |
| `riders/onboarding/` | POST | Onboard new rider |
| `s3/presigned-url/` | GET | S3 presigned URL for uploads |
| `activity/` | GET | Activity feed |
| `ably-token/` | GET | Ably real-time token |

### 1.6 Wallet (`/api/wallet/`)

| URL | Method | View | Description |
|-----|--------|------|-------------|
| `paystack-key/` | GET | get_paystack_public_key | Paystack public key |
| `balance/` | GET | get_wallet_balance | Wallet balance |
| `transactions/` | GET | get_transaction_history | Transaction history |
| `fund/initialize/` | POST | initialize_payment | Initialize payment |
| `fund/verify/` | POST | verify_payment | Verify payment |
| `webhook/` | POST | paystack_webhook | Paystack webhook |
| `virtual-account/` | GET | get_virtual_account | Virtual account details |
| `fund/transfer-claim/` | POST | confirm_transfer_payment | Confirm bank transfer |
| `corebanking-webhook/` | POST | corebanking_webhook | LibertyPay webhook |

### 1.7 Bot (`/api/bot/`)

| URL | Method | View | Description |
|-----|--------|------|-------------|
| `lookup/` | POST | MerchantLookupView | Lookup merchant by API key |
| `signup/` | POST | QuickSignupView | Quick signup via bot |
| `summary/` | GET | DashboardSummaryView | Dashboard summary |
| `orders/get-price/` | POST | GetPriceQuoteView | Price quote |
| `orders/create/` | POST | CreateOrderView | Create order via bot |
| `orders/` | GET | ListOrdersView | List orders |
| `orders/<order_number>/` | GET | OrderDetailView | Order detail |
| `orders/<order_number>/cancel/` | POST | CancelOrderView | Cancel order |
| `wallet/balance/` | GET | WalletBalanceView | Wallet balance |
| `wallet/transactions/` | GET | TransactionHistoryView | Transaction history |
| `wallet/virtual-account/` | GET | GetVirtualAccountView | Virtual account |

### 1.8 Webhooks (`/api/webhooks/`)

| URL | Method | View | Description |
|-----|--------|------|-------------|
| `config/` | GET, POST | WebhookCreateUpdateView | Manage webhook config |

---

## 2. Endpoint-to-OCC Data Mapping

### Orders

| OCC Need | Available? | Endpoint | Notes |
|----------|-----------|----------|-------|
| Order list with status & timestamps | ✅ Yes | `GET /api/dispatch/orders/` | Has status, created_at, picked_up_at, completed_at, canceled_at |
| Order detail (rider, merchant, zone) | ✅ Yes | `GET /api/dispatch/orders/<order_number>/` | Full detail with deliveries |
| Order stats (totals, revenue) | ⚠️ Partial | `GET /api/orders/stats/` | Merchant-scoped only — no admin/global scope |
| Assign rider to order | ✅ Yes | `POST /api/dispatch/orders/<id>/assign_rider/` | Available |
| Update order status | ✅ Yes | `POST /api/dispatch/orders/<id>/update_status/` | Available |
| Order events (status transitions) | ✅ Yes | Embedded in `OrderEvent` model | Available via order detail |
| Distance & delivery fee | ✅ Yes | Fields on Order model | `distance_km`, `total_amount` |
| Acceptance/rejection tracking | ⚠️ Partial | `OrderOffer` model exists | No admin-facing analytics endpoint |
| Failed delivery reason | ❌ No | — | No `failure_reason` field on Delivery model |

### Riders

| OCC Need | Available? | Endpoint | Notes |
|----------|-----------|----------|-------|
| Rider profile (name, phone, zone, bike) | ✅ Yes | `GET /api/dispatch/riders/<id>/` | Full profile with vehicle, zone |
| Online/offline status | ✅ Yes | `Rider.status` field | online / on_delivery / offline |
| GPS coordinates | ✅ Yes | `RiderLocation` model | Updated via `POST /api/riders/location/update/` |
| Last active timestamp | ✅ Yes | `Rider.last_seen_at` | Available |
| Per-period aggregates (orders, revenue) | ❌ No | — | Must compute from raw Order queries |
| Distance covered per period | ❌ No | — | `VehicleAsset.distance_today` exists but no history |
| Peak hour activity (12–3pm, 5–8pm) | ❌ No | — | No duty log tracking on/off transitions |
| CSAT per delivery | ❌ No | — | `Rider.rating` is aggregate only; no per-order ratings |
| Ghost ride detection | ❌ No | — | Status + GPS data exist separately; no computed flag |
| Rider earnings (admin view) | ❌ No | — | `RiderEarning` model exists but endpoint is rider-scoped only |
| Bulk rider locations (map) | ❌ No | — | No endpoint to fetch all rider locations at once |

### Merchants

| OCC Need | Available? | Endpoint | Notes |
|----------|-----------|----------|-------|
| Merchant list (name, contact, phone) | ✅ Yes | `GET /api/dispatch/merchants/` | Has merchant_id, name, totalOrders, monthOrders, walletBalance |
| Merchant detail | ✅ Yes | `GET /api/dispatch/merchants/<id>/` | Profile data |
| Order history & revenue | ⚠️ Partial | `totalOrders`, `monthOrders` on serializer | No detailed analytics (avg order value, fulfillment rate) |
| Activity status (active/watch/inactive) | ❌ No | — | No field or classification logic |
| Zone assignment | ❌ No | — | No `zone` FK on Merchant model |
| Acquisition date & source | ⚠️ Partial | `User.created_at` | No `acquisition_source` field |
| Last order date / days since | ❌ No | — | Must be computed |

### Zones & Verticals

| OCC Need | Available? | Endpoint | Notes |
|----------|-----------|----------|-------|
| Zone list with coordinates | ✅ Yes | `GET /api/dispatch/zones/` | Name, center_lat/lng, radius_km |
| Zone CRUD | ✅ Yes | Full CRUD on ViewSet | Available |
| Vertical list | ❌ No | — | **Model exists** (`Vertical` with name, code, lead_name) but **zero API endpoints** |
| Orders/revenue per zone | ❌ No | — | No zone-level analytics endpoint |
| Rider/merchant count per zone | ❌ No | — | Must be computed; riders have `home_zone` FK but merchants don't |
| Zone targets | ❌ No | — | No `ZoneTarget` model |
| Vertical targets | ❌ No | — | No model or endpoint |

### Communications

| OCC Need | Available? | Endpoint | Notes |
|----------|-----------|----------|-------|
| Comms history (SMS, WhatsApp, email) | ❌ No | — | No communications models in this backend. **This will live entirely in the OCC.** |
| Rider in-app notifications | ✅ Yes | `RiderNotification` model | Can be created/pushed; has read tracking |

---

## 3. Identified Gaps

### 3A. Data Exists in DB — No Endpoint Exposed

| # | Gap | DB Source | What's Needed |
|---|-----|-----------|---------------|
| 1 | **Vertical endpoints** | `Vertical` model (dispatcher app) | ViewSet with list/detail + aggregate stats |
| 2 | **Rider earnings (admin view)** | `RiderEarning` model | Admin endpoint to query any rider's earnings |
| 3 | **Bulk rider locations** | `RiderLocation` model (OneToOne on Rider) | Single endpoint returning all rider GPS positions |
| 4 | **Order offer analytics** | `OrderOffer` model (pending/accepted/declined) | Acceptance rate calculation endpoint |
| 5 | **COD records analytics** | `RiderCodRecord` model (pending/remitted/verified) | Admin analytics endpoint |
| 6 | **Vehicle tracking history** | `VehicleTracking` model (GPS breadcrumbs) | Query endpoint for historical positions |
| 7 | **Rider documents (admin)** | `RiderDocument` model | Admin review/approve endpoint |

### 3B. Data Does NOT Exist at All

| # | Gap | OCC Need | What's Missing |
|---|-----|----------|----------------|
| 1 | **Ghost ride detection** | Rider offline but GPS shows movement | No computed field/flag combining `Rider.status` + `RiderLocation.speed` / `VehicleAsset.speed` |
| 2 | **Peak hour utilisation** | Was rider online during 12–3pm and 5–8pm? | No `RiderDutyLog` model tracking on/off transitions with timestamps |
| 3 | **Per-period rider aggregates** | Orders/revenue/distance per day/week/month | No `RiderDailySnapshot` or aggregate table |
| 4 | **Merchant activity status** | Active / Watch / Inactive classification | No field on `Merchant` model; no order frequency tracking |
| 5 | **Merchant zone assignment** | Which zone a merchant belongs to | No `zone` FK on `Merchant` or `User` model |
| 6 | **Merchant acquisition source** | How/where merchant was acquired | No `acquisition_source` field |
| 7 | **Merchant order aggregates** | Total orders, revenue, avg order value, fulfillment rate | No pre-aggregated table |
| 8 | **Distance per rider per period** | Historical KM tracking | `VehicleAsset.distance_today` resets daily; no historical log |
| 9 | **CSAT per delivery** | Customer satisfaction per order | `Rider.rating` is aggregate only; no per-order `DeliveryRating` model |
| 10 | **Zone targets** | Monthly order/revenue targets per zone | No `ZoneTarget` model |
| 11 | **Vertical targets** | Monthly targets per vertical | No model |
| 12 | **Zone Captain role** | User role for zone management | Not in `User.usertype` choices (only Merchant/Rider/Customer/Dispatcher) |
| 13 | **Vertical Lead role** | User role for vertical management | Not in `User.usertype` choices |
| 14 | **Communications log** | Messages sent to riders/merchants | No comms model — **will live entirely in OCC** |
| 15 | **Failed delivery reason** | Why a delivery failed | `Order.cancellation_reason` exists but no `failure_reason` on Delivery |
| 16 | **Order rejection reason** | Why rider declined an order | `OrderOffer.status` tracks declined but no `decline_reason` field |

---

## 4. Endpoints to Build

### 4.1 Vertical & Zone Hierarchy

```
GET  /api/occ/verticals/
     Response: [{
       id, name, code, lead_name, zone_count, rider_count,
       merchant_count, orders_count, revenue, target_attainment_pct
     }]
     Query params: ?period=today|this_week|this_month|last_month|<YYYY-MM>

GET  /api/occ/verticals/<id>/
     Response: {
       id, name, code, lead_name,
       zones: [{id, name, captain, orders, revenue, target_pct, status}],
       aggregates: {
         orders, revenue, active_riders, active_merchants, target_attainment_pct
       }
     }

GET  /api/occ/verticals/<id>/zones/
     Response: [{
       id, name, captain, rider_count, merchant_count,
       orders, revenue, target_attainment_pct, status
     }]
```

### 4.2 Zone-Level Analytics

```
GET  /api/occ/zones/<id>/dashboard/
     Response: {
       orders_total, orders_completed, orders_failed, revenue,
       rider_count, active_riders, merchant_count, active_merchants,
       target_attainment_pct, avg_delivery_time
     }
     Query params: ?period=today|this_week|this_month|last_month|<YYYY-MM>

GET  /api/occ/zones/<id>/riders/
     Response: [{
       id, name, phone, status, orders_completed, orders_rejected,
       orders_failed, revenue, distance_km, acceptance_rate,
       ghost_ride_flag, peak_hour_pct, csat, online_days_ratio
     }]
     Query params: ?period=...

GET  /api/occ/zones/<id>/merchants/
     Response: [{
       id, name, contact, phone, activity_status, total_orders,
       revenue, avg_order_value, fulfillment_rate, last_order_date,
       days_since_last_order
     }]
     Query params: ?period=...
```

### 4.3 Rider Performance Analytics

```
GET  /api/occ/riders/<id>/performance/
     Response: {
       km_to_revenue_ratio,
       online_vs_offline_days,
       acceptance_rate,
       ghost_ride_ratio,
       avg_delivery_time_minutes,
       csat_rating,
       failed_delivery_rate,
       peak_hour_utilisation,
       revenue_per_km,
       orders: {total, completed, rejected, failed},
       anomaly_flags: [{metric, severity, message}]
     }
     Query params: ?period=today|this_week|this_month|...

GET  /api/occ/riders/locations/
     Response: [{
       rider_id, name, latitude, longitude, status,
       speed, is_moving, last_updated, zone
     }]
     (Bulk GPS endpoint for map view)
```

### 4.4 Merchant Analytics

```
GET  /api/occ/merchants/<id>/analytics/
     Response: {
       total_orders, revenue, avg_order_value, fulfillment_rate,
       order_frequency_per_day, last_order_date, days_since_last_order,
       activity_status, acquisition_date, zone
     }
     Query params: ?period=...
```

### 4.5 Leaderboards & Targets

```
GET  /api/occ/leaderboard/zones/
     Response: [{
       zone_id, zone_name, captain, orders, revenue, target_pct,
       rank, earnings: {base, transport, commission, total}
     }]
     Query params: ?period=...

GET  /api/occ/leaderboard/verticals/
     Response: [{
       vertical_id, name, lead_name, orders, revenue, target_pct,
       rank, earnings: {base, transport, commission, total}
     }]
     Query params: ?period=...
```

### 4.6 Order Analytics (Admin/OCC Scoped)

```
GET  /api/occ/orders/analytics/
     Response: {
       total, completed, failed, canceled, pending,
       revenue, avg_delivery_fee, avg_distance_km,
       avg_delivery_time_minutes,
       by_zone: [{zone_id, zone_name, orders, revenue}],
       by_hour: [{hour, orders}]
     }
     Query params: ?period=...&zone=...&vertical=...
```

---

## 5. DB Schema Gaps — Models & Fields to Add

### 5.1 New Models

#### `ZoneCaptain` — Links a user to a zone as its captain

```python
# dispatcher/models.py

class ZoneCaptain(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="zone_captain_profile")
    zone = models.OneToOneField(Zone, on_delete=models.CASCADE, related_name="captain")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### `VerticalLead` — Links a user to a vertical as its lead

```python
class VerticalLead(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="vertical_lead_profile")
    vertical = models.OneToOneField(Vertical, on_delete=models.CASCADE, related_name="lead")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### `RiderDutyLog` — Tracks on/off duty transitions for peak-hour analysis

```python
# riders/models.py (or dispatcher/models.py)

class RiderDutyLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name="duty_logs")
    went_online = models.DateTimeField()
    went_offline = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
```

#### `RiderDailySnapshot` — Pre-aggregated daily metrics per rider

```python
class RiderDailySnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name="daily_snapshots")
    date = models.DateField(db_index=True)
    orders_completed = models.IntegerField(default=0)
    orders_rejected = models.IntegerField(default=0)
    orders_failed = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    online_minutes = models.IntegerField(default=0)
    peak_hour_minutes = models.IntegerField(default=0)   # 12–3pm + 5–8pm
    ghost_ride_minutes = models.IntegerField(default=0)   # offline but GPS moving

    class Meta:
        unique_together = ("rider", "date")
```

#### `MerchantDailySnapshot` — Pre-aggregated daily metrics per merchant

```python
class MerchantDailySnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    merchant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="merchant_daily_snapshots")
    date = models.DateField(db_index=True)
    orders_placed = models.IntegerField(default=0)
    orders_completed = models.IntegerField(default=0)
    orders_failed = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        unique_together = ("merchant", "date")
```

#### `DeliveryRating` — Per-delivery CSAT rating

```python
# orders/models.py

class DeliveryRating(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="rating")
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name="delivery_ratings")
    score = models.IntegerField()   # 1–5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### `ZoneTarget` — Monthly targets per zone

```python
# dispatcher/models.py

class ZoneTarget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name="targets")
    month = models.DateField()   # first of month
    target_orders = models.IntegerField(default=2000)     # 5 riders × 400
    target_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=600000)

    class Meta:
        unique_together = ("zone", "month")
```

#### `ServiceAPIKey` — API keys for server-to-server auth

```python
# dispatcher/models.py

class ServiceAPIKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)               # e.g. "OCC Production"
    key_hash = models.CharField(max_length=255, unique=True)  # SHA-256 hash
    prefix = models.CharField(max_length=8, unique=True)      # first 8 chars for DB lookup
    scopes = models.JSONField(default=list)                # ["occ:read", "occ:write"]
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
```

### 5.2 Fields to Add to Existing Models

#### On `Merchant` model (`dispatcher/models.py`)

```python
zone = models.ForeignKey(Zone, null=True, blank=True, on_delete=models.SET_NULL, related_name="merchants")
acquisition_source = models.CharField(max_length=100, blank=True)   # "experiential", "referral", "organic"
activity_status = models.CharField(
    max_length=20,
    choices=[("active", "Active"), ("watch", "Watch"), ("inactive", "Inactive")],
    default="active"
)
last_order_date = models.DateTimeField(null=True, blank=True)
```

#### On `User` model (`authentication/models.py`)

```python
# Extend usertype choices to include OCC roles:
usertype = CharField(choices=[
    ("Merchant", "Merchant"),
    ("Rider", "Rider"),
    ("Customer", "Customer"),
    ("Dispatcher", "Dispatcher"),
    ("ZoneCaptain", "Zone Captain"),      # NEW
    ("VerticalLead", "Vertical Lead"),    # NEW
])
```

#### On `OrderOffer` model (`riders/models.py`)

```python
decline_reason = models.CharField(max_length=255, blank=True)
```

#### On `Delivery` model (`orders/models.py`)

```python
failure_reason = models.CharField(max_length=255, blank=True)
```

---

## 6. Inter-Project Auth Proposal

### Approach: Scoped Service API Keys via `Authorization: Bearer sk_...`

The bot module already uses `BotAPIKeyAuthentication` with `X-API-Key`. For OCC, a more robust version is recommended with hashed keys, scopes, and expiry.

### 6.1 Key Generation — Management Command

```python
# dispatcher/management/commands/create_service_key.py

import secrets
import hashlib
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from dispatcher.models import ServiceAPIKey


class Command(BaseCommand):
    help = "Generate a service API key for inter-project auth"

    def add_arguments(self, parser):
        parser.add_argument("name", type=str, help="Key name, e.g. 'OCC Production'")
        parser.add_argument("--scopes", nargs="+", default=["occ:read"])
        parser.add_argument("--expires-days", type=int, default=365)

    def handle(self, *args, **options):
        raw_key = "sk_" + secrets.token_urlsafe(48)
        prefix = raw_key[:11]    # "sk_" + first 8 of token
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        ServiceAPIKey.objects.create(
            name=options["name"],
            prefix=prefix,
            key_hash=key_hash,
            scopes=options["scopes"],
            expires_at=timezone.now() + timedelta(days=options["expires_days"]),
        )

        self.stdout.write(self.style.SUCCESS(
            f"\nAPI Key created: {options['name']}\n"
            f"Scopes: {options['scopes']}\n"
            f"Key (store securely — shown ONCE):\n\n  {raw_key}\n"
        ))
```

**Usage:**

```bash
python manage.py create_service_key "OCC Production" --scopes occ:read occ:write
python manage.py create_service_key "OCC Staging" --scopes occ:read --expires-days 90
```

### 6.2 Authentication Class

```python
# dispatcher/authentication.py

import hashlib
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone
from dispatcher.models import ServiceAPIKey


class ServiceUser:
    """Dummy user object for service-to-service auth."""
    is_authenticated = True
    is_active = True
    is_staff = False
    is_superuser = False
    pk = None
    id = None

    def __init__(self, api_key):
        self.api_key = api_key
        self.scopes = api_key.scopes
        self.service_name = api_key.name


class ServiceAPIKeyAuthentication(BaseAuthentication):
    """
    Authenticates requests from the OCC backend using:
        Authorization: Bearer sk_xxxxx...
    """
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith(f"{self.keyword} sk_"):
            return None   # Not our auth scheme — let other authenticators try

        raw_key = auth_header[len(self.keyword) + 1:]
        prefix = raw_key[:11]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        try:
            api_key = ServiceAPIKey.objects.get(
                prefix=prefix,
                key_hash=key_hash,
                is_active=True,
            )
        except ServiceAPIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid service API key.")

        if api_key.expires_at and api_key.expires_at < timezone.now():
            raise AuthenticationFailed("Service API key has expired.")

        # Track last usage
        api_key.last_used_at = timezone.now()
        api_key.save(update_fields=["last_used_at"])

        return (ServiceUser(api_key), api_key)
```

### 6.3 Permission Classes

```python
# dispatcher/permissions.py

from rest_framework.permissions import BasePermission


class HasOCCReadScope(BasePermission):
    """Allows access if the service key has 'occ:read' or 'occ:*' scope."""

    def has_permission(self, request, view):
        user = request.user
        if hasattr(user, "scopes"):
            return "occ:read" in user.scopes or "occ:*" in user.scopes
        return False


class HasOCCWriteScope(BasePermission):
    """Allows access if the service key has 'occ:write' or 'occ:*' scope."""

    def has_permission(self, request, view):
        user = request.user
        if hasattr(user, "scopes"):
            return "occ:write" in user.scopes or "occ:*" in user.scopes
        return False
```

### 6.4 Applying Auth to OCC Views

```python
# dispatcher/occ_views.py (example)

from rest_framework.views import APIView
from rest_framework.response import Response
from dispatcher.authentication import ServiceAPIKeyAuthentication
from dispatcher.permissions import HasOCCReadScope


class VerticalListView(APIView):
    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOCCReadScope]

    def get(self, request):
        period = request.query_params.get("period", "this_month")
        # ... build response
        return Response(data)
```

### 6.5 URL Configuration

```python
# ax_merchant_api/urls.py — add this line:

urlpatterns = [
    # ... existing patterns ...
    path("api/occ/", include("dispatcher.occ_urls")),
]
```

```python
# dispatcher/occ_urls.py

from django.urls import path
from dispatcher.occ_views import (
    VerticalListView, VerticalDetailView,
    ZoneDashboardView, ZoneRidersView, ZoneMerchantsView,
    RiderPerformanceView, RiderLocationsView,
    MerchantAnalyticsView,
    ZoneLeaderboardView, VerticalLeaderboardView,
    OrderAnalyticsView,
)

urlpatterns = [
    path("verticals/", VerticalListView.as_view()),
    path("verticals/<uuid:id>/", VerticalDetailView.as_view()),
    path("zones/<uuid:id>/dashboard/", ZoneDashboardView.as_view()),
    path("zones/<uuid:id>/riders/", ZoneRidersView.as_view()),
    path("zones/<uuid:id>/merchants/", ZoneMerchantsView.as_view()),
    path("riders/<uuid:id>/performance/", RiderPerformanceView.as_view()),
    path("riders/locations/", RiderLocationsView.as_view()),
    path("merchants/<uuid:id>/analytics/", MerchantAnalyticsView.as_view()),
    path("leaderboard/zones/", ZoneLeaderboardView.as_view()),
    path("leaderboard/verticals/", VerticalLeaderboardView.as_view()),
    path("orders/analytics/", OrderAnalyticsView.as_view()),
]
```

### 6.6 How the OCC Backend Calls This API

```python
# In the OCC Django project — services/axpress_client.py

import os
import requests

AXPRESS_API_URL = os.environ["AXPRESS_API_URL"]       # https://api.axpress.net
AXPRESS_SERVICE_KEY = os.environ["AXPRESS_SERVICE_KEY"]  # sk_xxxxx...


def axpress_get(path, params=None):
    """Make an authenticated GET request to the main AXpress backend."""
    response = requests.get(
        f"{AXPRESS_API_URL}{path}",
        headers={"Authorization": f"Bearer {AXPRESS_SERVICE_KEY}"},
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


# Usage examples:
verticals = axpress_get("/api/occ/verticals/", {"period": "this_month"})
zone_riders = axpress_get(f"/api/occ/zones/{zone_id}/riders/", {"period": "this_week"})
rider_perf = axpress_get(f"/api/occ/riders/{rider_id}/performance/", {"period": "today"})
```

### 6.7 Environment Variables

**Main backend (`.env`):**
```
# No new env vars needed — keys are generated via management command
# and stored in the ServiceAPIKey database table
```

**OCC backend (`.env`):**
```
AXPRESS_API_URL=https://api.axpress.net
AXPRESS_SERVICE_KEY=sk_<the-key-from-create_service_key-command>
```

---

## 7. Summary

### Coverage Matrix

| Category | Existing Endpoints | Gaps (data exists, no endpoint) | Gaps (no data at all) |
|----------|-------------------|--------------------------------|----------------------|
| **Orders** | 15+ endpoints | Admin-scoped analytics | Failed delivery reason, per-hour breakdown |
| **Riders** | 20+ endpoints | Bulk locations, earnings (admin), offer analytics | Duty logs, daily snapshots, ghost detection, peak hours, per-delivery CSAT |
| **Merchants** | CRUD exists | Activity classification | Zone FK, acquisition source, daily snapshots |
| **Zones** | CRUD exists | — | Zone targets, captain role |
| **Verticals** | Model exists | **No endpoint at all** | Lead role, targets |
| **Auth** | JWT + Bot API key | — | Service API key model |
| **Comms** | Rider notifications | — | **Entirely OCC-side** |

### Priority Build Items

| # | Item | Effort | Why |
|---|------|--------|-----|
| 1 | **`ServiceAPIKey` model + auth class** | Small | Unblocks all OCC integration — build this first |
| 2 | **`Vertical` ViewSet + OCC endpoints** | Medium | Model exists with zero exposure; OCC hierarchy depends on it |
| 3 | **`RiderDailySnapshot` + `MerchantDailySnapshot` + Celery task** | Medium | Powers all period-based analytics without hammering raw Order table |
| 4 | **`RiderDutyLog` model + hook into `toggle_duty` view** | Small | Required for peak-hour and online/offline ratio metrics |
| 5 | **`DeliveryRating` model** | Small | Per-delivery CSAT; currently only one aggregate `Rider.rating` |
| 6 | **`ZoneCaptain` + `VerticalLead` models** | Small | Formalizes the OCC role hierarchy |
| 7 | **`ZoneTarget` model** | Small | Stores configurable monthly targets per zone |
| 8 | **Merchant fields** (`zone`, `activity_status`, `acquisition_source`, `last_order_date`) | Small | Missing FK and classification fields |
| 9 | **OCC analytics views** (10–12 endpoints) | Large | The actual API surface the OCC dashboard consumes |
| 10 | **Ghost ride detection** (in daily snapshot Celery task) | Medium | Compare `Rider.status == offline` with `VehicleAsset.speed > 0` |

### Existing DB Models (42 total across 8 apps)

- **Orders app:** Vehicle, MerchantPricingOverride, Order, Delivery, OrderEvent, OrderLeg
- **Riders app:** RiderAuth, RiderSession, RiderCodRecord, RiderEarning, RiderDocument, OrderOffer, RiderDevice, AreaDemand, RiderNotification, RiderLocation, RideToOwnConfig, RideToOwnEnrollment, RiderMonthlyTarget, RiderStreak, Challenge, RiderChallengeProgress, LeaderboardEntry
- **Authentication app:** User, Address
- **Dispatcher app:** Vertical, Zone, RelayNode, VehicleAsset, VehicleTracking, Rider, DispatcherProfile, Merchant, SystemSettings, ActivityFeed
- **Wallet app:** Wallet, Transaction, VirtualAccount, WebhookLog
- **Referrals app:** RiderReferral, ReferralEarning
- **Webhooks app:** Webhook, WebhookOutbox

### Existing Infrastructure

- PostgreSQL database
- Redis (cache + sessions + Celery broker)
- Ably (real-time messaging)
- Google Maps API (geocoding/directions)
- Paystack (payments)
- Mailgun (emails)
- AWS S3 (document/image storage)
- LibertyPay CoreBanking API
- Respond.io (WhatsApp)
