# AXpress Operations Dashboard API — Frontend / Postman Guide

Reference for every **Operations Dashboard** endpoint (`/api/ops/…`): URL, auth, query params,
request payload, and an example response. Share this with the frontend.

---

## 1. Base URL & authentication

| Env | Base URL |
|---|---|
| Local | `http://localhost:8000` |
| Production | `https://<your-domain>` |

All endpoints are **server-to-server** and authenticated with a **Service API Key** (the same keys
used for `/api/occ/`). Send it as a Bearer token on **every** request:

```
Authorization: Bearer sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- Read endpoints (`GET`) require the **`occ:read`** scope.
- Write endpoints (`POST` / `PUT` / `PATCH`) require the **`occ:write`** scope.

**Suggested Postman variables:** `{{base_url}}` and `{{service_key}}`, with a collection-level header
`Authorization: Bearer {{service_key}}`.

Auth failures:
- Missing/invalid key → **`403 Forbidden`** (or `401`), body `{ "detail": "..." }`.
- Write endpoint with a read-only key → **`403 Forbidden`**.

---

## 2. Standard response envelope

Every successful dashboard response uses this envelope:

```json
{
  "success": true,
  "data": { },
  "date_range": { "filter": "this_month", "start": "2026-06-01T00:00:00+01:00", "end": "2026-06-27T12:00:00+01:00" }
}
```

- `data` — the endpoint payload (object or, for lists, an object containing `results` + pagination).
- `date_range` — echoes the applied filter; `null` on endpoints that take no date filter.

**Error shape:**
```json
{ "success": false, "detail": "Human-readable message." }
```
Validation errors (rule edits) use: `{ "success": false, "errors": { "field": ["msg"] } }`.

---

## 3. The general date filter (applies to every dashboard GET)

`order-dashboard`, `payments`, `cod-dashboard`, `alert-dashboard`, and `fuel-dashboard` all accept the
**same** filter via `?filter=`. (`tracking-dashboard` is a **live** snapshot and takes no date filter.)
Filter values:

| `filter` | Extra params | Meaning |
|---|---|---|
| `today` | — | current day |
| `this_week` | — | Monday → now |
| `this_month` | — | 1st → now |
| `annually` | — | Jan 1 → now (this year) |
| `single_date` | `date=YYYY-MM-DD` | one specific day |
| `date_range` | `start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` | inclusive range |

Default when omitted: `this_month`. (Legacy `?period=today|this_week|this_month|this_year|YYYY-MM`
is still accepted.)

> **Caching:** `order-dashboard`, `payments`, `cod-dashboard`, and `fuel-dashboard` are cached and
> pre-warmed every 30 min by a background task, so their data may be up to ~30 minutes stale.
> `alert-dashboard` and `tracking-dashboard` are always live.

Examples:
```
GET {{base_url}}/api/ops/payments/?filter=today
GET {{base_url}}/api/ops/fuel-dashboard/?filter=single_date&date=2026-06-26
GET {{base_url}}/api/ops/cod-dashboard/?filter=date_range&start_date=2026-06-01&end_date=2026-06-30
```

---

## 4. Endpoints

### 4.1 Health — `GET /api/ops/health/`
Connectivity / auth check. Scope: `occ:read`.

**Query:** `period` (optional). **Body:** none.

**200 Response**
```json
{
  "success": true,
  "data": { "app": "oprtn_dashboard", "status": "ok", "phase": 4 },
  "date_range": { "filter": "this_month", "start": "2026-06-01T00:00:00+01:00", "end": "2026-06-27T12:00:00+01:00" }
}
```

---

### 4.2 List alerts — `GET /api/ops/alerts/`
Scope: `occ:read`.

**Query params**
| Param | Default | Values |
|---|---|---|
| `status` | `active` | `active` (new+investigating), `all`, `new`, `investigating`, `resolved`, `false_positive` |
| `type` | — | an `alert_type` (e.g. `BIKE_AFTER_HOURS`) |
| `severity` | — | `low`, `medium`, `high`, `critical` |
| `entity_type` | — | `rider`, `order`, `merchant`, `vehicle`, `zone`, `system` |
| `page` | `1` | page number |
| `page_size` | `25` | max `100` |

**200 Response**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "0e7c…", "alert_type": "BIKE_AFTER_HOURS", "severity": "high",
        "entity_type": "vehicle", "title": "Bike EPE440QS moving after hours",
        "description": "30 km/h at 22:14 (curfew 20:00–06:00).",
        "value": "30.00", "context": { "plate_number": "EPE440QS", "speed_kmh": "30" },
        "dedupe_key": "BIKE_AFTER_HOURS:<vehicle_id>:2026-06-26",
        "status": "new", "resolution_note": "", "resolved_at": null,
        "first_seen_at": "2026-06-26T22:14:00+01:00", "last_seen_at": "2026-06-26T22:24:00+01:00",
        "created_at": "2026-06-26T22:14:00+01:00", "updated_at": "2026-06-26T22:24:00+01:00",
        "rider": "<rider_uuid|null>", "order": null, "merchant": null,
        "vehicle": "<vehicle_uuid>", "zone": null,
        "rider_code": "841149", "order_number": null, "vehicle_plate": "EPE440QS"
      }
    ],
    "count": 1, "page": 1, "page_size": 25, "total_pages": 1
  },
  "date_range": null
}
```

---

### 4.3 Alert detail — `GET /api/ops/alerts/{id}/`
Scope: `occ:read`. **Body:** none.

**200** → `data` is a single alert object (same shape as an item in 4.2).
**404** → `{ "success": false, "detail": "Not found." }`

---

### 4.4 Resolve / update an alert — `POST` or `PATCH /api/ops/alerts/{id}/resolve/`
Scope: `occ:write`.

**Request body**
```json
{ "status": "resolved", "resolution_note": "Checked with rider, false alarm." }
```
- `status` (optional, default `resolved`): `resolved` | `false_positive` | `investigating`.
- `resolution_note` (optional string).

**200** → `data` is the updated alert object.
**400** → invalid status. **404** → not found.

---

### 4.5 Run the alert engine — `POST /api/ops/alerts/generate/`
Scope: `occ:write`. Evaluates enabled rules now (also runs automatically every 30 min).

**Request body** (optional — omit to run all rules)
```json
{ "types": ["BIKE_AFTER_HOURS", "INCOMPLETE_ORDER"] }
```

**200 Response**
```json
{
  "success": true,
  "data": { "evaluated": 13, "created": 2, "updated": 1, "resolved": 1, "skipped": 0,
            "no_evaluator": ["COD_GAP", "HIGH_CANCELLATION"] },
  "date_range": null
}
```

---

### 4.6 Alert dashboard — `GET /api/ops/alert-dashboard/`
Scope: `occ:read`. Honours the **general filter** (§3) + `limit` (recent list size, default 20).

**200 Response**
```json
{
  "success": true,
  "data": {
    "period_summary": {
      "total": 42,
      "by_status": { "new": 12, "investigating": 3, "resolved": 25, "false_positive": 2 },
      "by_severity": { "critical": 5, "high": 18, "medium": 15, "low": 4 },
      "resolution_rate": 64.3
    },
    "period_by_type": [ { "alert_type": "GPS_OFFLINE", "count": 14 }, { "alert_type": "SPEED_VIOLATION", "count": 9 } ],
    "active": {
      "total": 15,
      "by_severity": { "critical": 2, "high": 8, "medium": 4, "low": 1 },
      "by_type": [ { "alert_type": "INCOMPLETE_ORDER", "count": 6 } ]
    },
    "recent_active": [ /* array of alert objects, newest first (see 4.2) */ ]
  },
  "date_range": { "filter": "this_month", "start": "…", "end": "…" }
}
```

---

### 4.7 List alert rules — `GET /api/ops/alert-rules/`
Scope: `occ:read`. **Query:** `is_enabled=true|false` (optional).

**200 Response**
```json
{
  "success": true,
  "data": [
    {
      "id": "…", "alert_type": "BIKE_AFTER_HOURS", "is_enabled": true,
      "default_severity": "high", "warn_threshold": null, "critical_threshold": null,
      "window_minutes": 10,
      "params": { "curfew_start_hour": 20, "curfew_end_hour": 6, "vehicle_types": ["bike"], "min_speed_kmh": 5 },
      "description": "Bike moving between 20:00 and 06:00.",
      "updated_at": "2026-06-27T09:00:00+01:00"
    }
  ],
  "date_range": null
}
```

---

### 4.8 Get / edit an alert rule — `GET` · `PUT` · `PATCH /api/ops/alert-rules/{id}/`
`GET` scope `occ:read`; `PUT`/`PATCH` scope `occ:write`.

**PATCH body** (any subset; `alert_type` is read-only)
```json
{ "is_enabled": false, "warn_threshold": "80", "critical_threshold": "120",
  "window_minutes": 15, "default_severity": "critical",
  "params": { "curfew_start_hour": 21 }, "description": "Tweaked" }
```

**200** → `data` is the updated rule. **400** → `{ "success": false, "errors": {…} }`. **404** → not found.

---

### 4.9 Payments (order amount by payment type) — `GET /api/ops/payments/`
Scope: `occ:read`. Honours the **general filter** (§3). Money values are **strings**.

**200 Response**
```json
{
  "success": true,
  "data": {
    "total_orders": 3,
    "total_amount": "2300.00",
    "recognized_revenue": "1500.00",
    "by_method": [
      { "payment_method": "wallet", "count": 1, "amount": "1000.00", "pct": 43.5, "collection_timing": "prepaid" },
      { "payment_method": "postpaid", "count": 1, "amount": "800.00", "pct": 34.8, "collection_timing": "deferred" },
      { "payment_method": "cash", "count": 1, "amount": "500.00", "pct": 21.7, "collection_timing": "rider_collected" }
    ],
    "by_status": [ { "payment_status": "Paid", "count": 2, "amount": "1500.00", "pct": 65.2 } ],
    "by_collection_timing": {
      "prepaid": { "amount": "1000.00", "pct": 43.5 },
      "rider_collected": { "amount": "500.00", "pct": 21.7 },
      "deferred": { "amount": "800.00", "pct": 34.8 },
      "other": { "amount": "0", "pct": 0.0 }
    }
  },
  "date_range": { "filter": "this_month", "start": "…", "end": "…" }
}
```
> `total_amount` = all order delivery charges; `recognized_revenue` = delivered (`Done`) only.
> Payment methods: `wallet, cash, cash_on_pickup, receiver_pays, postpaid, subscription`.

---

### 4.9.1 Payment orders (drill-down) — `GET /api/ops/payments/orders/`
Scope: `occ:read`. Honours the **general filter** (§3). Lists the **actual orders** behind the
payments breakdown, with full order detail — drill into any `by_method` / `by_status` /
`by_collection_timing` bucket.

**Query params**
| Param | Values |
|---|---|
| `method` | a `payment_method` (e.g. `cash_on_pickup`) |
| `payment_status` | `Paid`, `Pending`, `Cancelled`, `Postpaid`, `Failed`, `Refunded` |
| `collection_timing` | `prepaid` (wallet) · `rider_collected` (cash/cash_on_pickup/receiver_pays) · `deferred` (postpaid/subscription) · `other` |
| `page`, `page_size` | pagination (default 25, max 100) |

Combine with the date filter (§3) and each other. Example:
`GET /api/ops/payments/orders/?filter=this_month&method=cash_on_pickup&page_size=20`

**200 Response**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "445d8030-…", "order_number": "6158078", "status": "Pending",
        "total_amount": "5787.00", "payment_method": "cash_on_pickup",
        "payment_status": "Pending", "collect_on_delivery": true, "cod_amount": "9341.00",
        "distance_km": "6.00", "duration_minutes": 49,
        "pickup_address": "12 Marina Rd, Lagos Island",
        "sender_name": "Seed Merchant 9", "sender_phone": "234815000008",
        "created_at": "2026-06-28T16:58:58+01:00", "assigned_at": null,
        "picked_up_at": null, "arrived_at": null, "completed_at": null, "canceled_at": null,
        "merchant": "Seed Merchant 9", "rider_code": "732107", "rider_name": "Seed Rider 4",
        "vehicle": "Bike",
        "deliveries": [
          { "receiver_name": "…", "receiver_phone": "…", "dropoff_address": "…",
            "status": "Pending", "cod_amount": "0.00" }
        ]
      }
    ],
    "filters": { "method": "cash_on_pickup", "payment_status": null, "collection_timing": null },
    "count": 20, "page": 1, "page_size": 20, "total_pages": 1
  },
  "date_range": { "filter": "this_month", "start": "…", "end": "…" }
}
```
> `deliveries` = the order's dropoff legs (multi-drop). `rider_code`/`rider_name` are null if unassigned.

---

### 4.10 COD dashboard — `GET /api/ops/cod-dashboard/`
Scope: `occ:read`. Honours the **general filter** (§3).

**200 Response**
```json
{
  "success": true,
  "data": {
    "cards": {
      "total_orders": 1, "delivered": 1, "in_progress": 0, "cancelled": 0,
      "cod_goods_value": "2000.00", "cod_expected": "2000.00",
      "cod_collected": "0.00", "cod_outstanding": "2000.00",
      "cod_fees_earned": "530.00", "delivery_rate": 100.0,
      "cod_fee_config": { "flat": "500.00", "pct": "1.50" },
      "source": { "cod_fees_earned": "estimated", "cod_collected": "actual" }
    },
    "ageing": {
      "0_24h": { "count": 1, "amount": "2000.00" },
      "24_48h": { "count": 0, "amount": "0" },
      "48h_plus": { "count": 0, "amount": "0" }
    },
    "top_riders": [ { "rider_id": "841149", "name": "Rider A", "orders": 1, "cod_amount": "2000.00" } ],
    "top_merchants": [ { "merchant": "TestMart", "orders": 1, "cod_amount": "2000.00" } ]
  },
  "date_range": { "filter": "this_month", "start": "…", "end": "…" }
}
```
> **COD fee** (`cod_fees_earned`) is AXpress revenue, computed `flat + pct% × cod_amount` — separate from
> the order amount and from the COD goods value. `cod_collected/outstanding` reconcile against rider remittances.

---

### 4.10.1 COD orders (drill-down) — `GET /api/ops/cod-dashboard/orders/`
Scope: `occ:read`. Honours the **general filter** (§3). Lists COD orders behind the COD dashboard,
each with its **COD settlement records** (`cod_records`).

**Query params**
| Param | Values |
|---|---|
| `rider` | a `rider_id` (drill into a `top_riders` row) |
| `merchant` | a `business_name` (drill into a `top_merchants` row) |
| `cod_status` | `collected` (has a remitted/verified record) · `pending` (outstanding) |
| `order_status` | `delivered`/`cancelled`/`in_progress`/`pending`/`failed` or a raw status |
| `page`, `page_size` | pagination |

**200 Response** — same order shape as §4.9.1 **plus** `cod_records`:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "order_number": "6158012", "status": "Done", "collect_on_delivery": true,
        "cod_amount": "12559.00", "merchant": "Seed Merchant 3",
        "rider_code": "732107", "rider_name": "Seed Rider 4",
        "cod_records": [
          { "status": "remitted", "amount": "12559.00",
            "remitted_at": "2026-06-29T11:58:58+01:00", "verified_at": null }
        ]
      }
    ],
    "filters": { "rider": null, "merchant": null, "cod_status": "collected", "order_status": null },
    "count": 5, "page": 1, "page_size": 25, "total_pages": 1
  },
  "date_range": { "filter": "this_month", "start": "…", "end": "…" }
}
```

---

### 4.11 Upload daily fuel bills — `POST /api/ops/fuel/upload/`
Scope: `occ:write`. **Content-Type:** `multipart/form-data`.

**Form-data**
| Key | Type | Notes |
|---|---|---|
| `file` | File | the `.xlsx` fuel bills export (exact bills format) |

Rows are upserted by **Invoice number** (idempotent — re-uploading the same file updates, never
duplicates). The "Vehicle" column (plate) is matched to a fleet vehicle/rider.

**200 Response**
```json
{
  "success": true,
  "data": {
    "total_rows": 358, "created": 354, "updated": 0, "skipped": 4,
    "unmatched_plates": ["EPE427QR", "EPE428QS"]
  },
  "date_range": null
}
```
**400** → `{ "success": false, "detail": "Upload an .xlsx file." }` (or "No file uploaded (field 'file').",
or "Unrecognized format: an 'Invoice number' column is required.")

> `unmatched_plates` = plates with no matching fleet `VehicleAsset` (still imported, just not linked to a rider).
> `skipped` = rows missing an invoice number or date.

---

### 4.12 Fuel dashboard — `GET /api/ops/fuel-dashboard/`
Scope: `occ:read`. Honours the **general filter** (§3), filtered on each bill's date.

**200 Response**
```json
{
  "success": true,
  "data": {
    "summary": {
      "records": 13, "total_cost": "63994.00", "total_liters": "52.532",
      "total_worker_tip": "560.000", "avg_fuel_price": "1221.45",
      "avg_km_per_l": "210.34", "source": "actual"
    },
    "by_vehicle": [ { "vehicle_plate": "FST908QR", "records": 1, "cost": "7400.00", "liters": "6.066" } ],
    "by_rider": [ { "rider_id": "841149", "name": "Rider A", "records": 1, "cost": "5000.00", "liters": "3.953" } ],
    "by_station": [ { "station": "Rainoil Limited", "records": 1, "cost": "5000.00" } ],
    "by_fuel_type": [ { "fuel_type": "Petrol", "records": 13, "cost": "63994.00", "liters": "52.532" } ],
    "daily_trend": [ { "date": "2026-06-26", "cost": "63994.00", "liters": "52.532", "records": 13 } ]
  },
  "date_range": { "filter": "single_date", "date": "2026-06-26", "start": "…", "end": "…" }
}
```

---

### 4.13 Order dashboard (consolidated) — `GET /api/ops/order-dashboard/`
Scope: `occ:read`. Honours the **general filter** (§3). Cached. Returns order metrics at three
levels: **management** (funnel + rates + revenue), **per-rider**, and **per-merchant**.

**200 Response**
```json
{
  "success": true,
  "data": {
    "management": {
      "total_orders": 90, "delivered": 50, "in_progress": 20, "pending": 10,
      "cancelled": 10, "failed": 0, "rejected": 0,
      "completion_rate": 55.6, "cancellation_rate": 11.1,
      "gross_revenue": "170888.00", "avg_order_value": "3417.76",
      "rider_commission_total": "34177.60", "commission_pct": "20"
    },
    "by_rider": [
      { "rider_id": "295570", "name": "Seed Rider 12", "orders": 4, "delivered": 2,
        "cancelled": 1, "completion_rate": 50.0, "revenue": "10593.00", "commission": "2118.60" }
    ],
    "by_merchant": [
      { "merchant": "Seed Merchant 2", "orders": 9, "delivered": 5, "cancelled": 1,
        "completion_rate": 55.6, "gmv": "21485.00", "avg_order_value": "4297.00" }
    ]
  },
  "date_range": { "filter": "this_month", "start": "…", "end": "…" }
}
```
> `in_progress` = "enroute" (statuses `Started/Pickup/Fulfilling/Arrived`). `delivered` = `Done`.
> `rider_commission_total` = `gross_revenue × commission_pct%` (rate from SystemSettings, default 20).
> `by_rider` / `by_merchant` are the top 10 by revenue.

---

### 4.13.1 Order orders (drill-down) — `GET /api/ops/order-dashboard/orders/`
Scope: `occ:read`. Honours the **general filter** (§3). Lists the orders behind the order dashboard —
drill into a per-rider or per-merchant row, or a status bucket. Full order detail (same shape as §4.9.1).

**Query params**
| Param | Values |
|---|---|
| `rider` | a `rider_id` |
| `merchant` | a `business_name` |
| `order_status` | `delivered`/`cancelled`/`in_progress`(=enroute)/`pending`/`failed`, or a raw status (e.g. `Started`) |
| `page`, `page_size` | pagination |

Example: `GET /api/ops/order-dashboard/orders/?filter=this_month&rider=732107&order_status=delivered`
→ `{ "data": { "results": [ …orders… ], "filters": {…}, "count": …, "page": …, "total_pages": … } }`

---

### 4.14 Tracking dashboard (live rider & vehicle) — `GET /api/ops/tracking-dashboard/`
Scope: `occ:read`. **Live snapshot — no date filter.** `?limit` controls the live list size
(default 50, max 200).

**200 Response**
```json
{
  "success": true,
  "data": {
    "as_of": "2026-06-29T12:00:00+01:00",
    "riders": {
      "total": 25, "online": 7, "on_delivery": 8, "offline": 10,
      "moving_now": 6, "gps_tracked": 25,
      "by_gps_status": { "moving": 6, "idle": 12, "offline": 7 }
    },
    "vehicles": {
      "total": 25, "active": 25, "assigned_to_rider": 25, "moving_now": 6,
      "with_telemetry": 25, "offline": 7,
      "by_engine_status": { "on": 6, "off": 12, "idle": 7, "unknown": 0 }
    },
    "live": [
      {
        "rider_id": "229883", "name": "Seed Rider 15",
        "rider_status": "online", "gps_status": "idle", "is_moving": false,
        "latitude": 6.442486, "longitude": 3.543536, "speed": 0.0,
        "last_location_update": "2026-06-29T11:31:52+01:00",
        "vehicle": {
          "asset_id": "AX-0015", "plate_number": "SEED-014", "vehicle_type": "van",
          "engine_status": "off", "tracking_status": "idle", "speed": 0.0,
          "last_telemetry_at": "2026-06-29T11:31:52+01:00"
        }
      }
    ]
  },
  "date_range": null
}
```
**Status meanings**
- `rider_status` (raw): `online` / `on_delivery` / `offline`.
- `gps_status` (derived): `moving` (is_moving) · `idle` (recent ping ≤2h, or online with coords) · `offline` (no ping >2h).
- vehicle `engine_status` (raw telemetry): `on` / `off` / `idle` / `unknown`.
- vehicle `tracking_status` (derived): `moving` (speed>0, fresh) · `idle` (fresh, speed 0) · `offline` (no telemetry >2h).
- `live[].vehicle` is the **VehicleAsset linked to that rider** (`null` if the rider has no assigned vehicle).

---

### 4.15 Overriding dashboard — `GET /api/ops/overriding-dashboard/`
Scope: `occ:read`. Honours the **general filter** (§3), on each order's `completed_at`.

For every delivered order, the rider's **actual km** (vehicle odometer delta between pickup and
completion, from GPS tracking) is compared to the **allowed km** = saved order estimate
(`distance_km`) + a fixed allowance (default **8 km**, from the `OVERRIDING` rule's
`params.allowance_km`). Anything above is **overriding km**, accumulated per rider with the
per-order breakdown of how it built up.

**Query params**: `?allowance_km=8` (override), `?top=10` (top-offenders list size).

**200 Response**
```json
{
  "success": true,
  "data": {
    "summary": {
      "allowance_km": 8.0, "orders_delivered": 40, "orders_checked": 36,
      "orders_no_estimate": 2, "orders_untracked": 2,
      "orders_with_overriding": 5, "riders_with_overriding": 3,
      "total_overriding_km": 41.5
    },
    "riders": [
      {
        "rider_id": "841149", "name": "Rider A", "plate_number": "EPE440QS",
        "orders_checked": 6, "orders_over": 2,
        "total_estimated_km": 51.0, "total_allowed_km": 99.0,
        "total_actual_km": 123.5, "total_overriding_km": 24.5,
        "orders": [
          { "order_number": "AX123", "completed_at": "…",
            "estimated_km": 10.0, "allowed_km": 18.0,
            "actual_km": 30.0, "overriding_km": 12.0 }
        ]
      }
    ],
    "top_riders": [ "…the top 10 riders with overriding_km > 0…" ]
  },
  "date_range": { "filter": "today", "start": "…", "end": "…" }
}
```
> `orders_untracked` = delivered orders with no usable GPS odometer snapshots;
> `orders_no_estimate` = orders without a saved `distance_km`. Neither can be scored.

---

### 4.16 Attendance dashboard — `GET /api/ops/attendance-dashboard/`
Scope: `occ:read`. Honours the **general filter** (§3), by calendar day (capped at the most
recent 31 days of the range).

Per rider, inside the daily **work window 08:00–22:00**: minutes **online vs offline** (from duty
sessions) against the **km the bike moved while online vs offline** (from GPS tracking).
Km moved while the rider was offline is flagged as **`riders_offline_moving`** — the bike is
out and moving but the rider isn't clocked in.

**Query params**: `?top=10` (top offline-moving list size).

**200 Response**
```json
{
  "success": true,
  "data": {
    "summary": {
      "work_window": "08:00–22:00", "days": 1, "days_truncated": false,
      "riders": 25, "riders_offline_moving": 2, "total_offline_moving_km": 12.4
    },
    "riders": [
      {
        "rider_id": "841149", "name": "Rider A", "plate_number": "EPE440QS",
        "status": "online",
        "online_minutes": 240, "offline_minutes": 600,
        "online_km": 10.0, "offline_moving_km": 7.0,
        "riders_offline_moving": true,
        "days": [
          { "date": "2026-07-03", "online_minutes": 240, "offline_minutes": 600,
            "online_km": 10.0, "offline_moving_km": 7.0 }
        ]
      }
    ],
    "top_offline_moving": [ "…top 10 riders by offline_moving_km…" ]
  },
  "date_range": { "filter": "single_date", "date": "2026-07-03", "start": "…", "end": "…" }
}
```

---

### 4.17 Revenue leaderboard — `GET /api/ops/revenue-leaderboard/`
Scope: `occ:read`. Honours the **general filter** (§3), on `completed_at`.

Riders ranked by **net revenue** (gross delivered revenue **minus their commission**,
rate from SystemSettings, default 20%). `top_riders` = the highest earners;
`bottom_riders` = the lowest **including riders with zero revenue** in the window.
`?top=20` sizes both lists.

**200 Response**
```json
{
  "success": true,
  "data": {
    "summary": {
      "riders_with_revenue": 12, "riders_total": 25,
      "gross_revenue": "412000.00", "commission_total": "82400.00",
      "net_revenue": "329600.00", "commission_pct": "20"
    },
    "top_riders": [
      { "rider_id": "841149", "name": "Rider A", "delivered": 30,
        "gross_revenue": "15000.00", "commission": "3000.00", "net_revenue": "12000.00" }
    ],
    "bottom_riders": [
      { "rider_id": "229883", "name": "Rider Z", "delivered": 0,
        "gross_revenue": "0.00", "commission": "0.00", "net_revenue": "0.00" }
    ]
  },
  "date_range": { "filter": "this_month", "start": "…", "end": "…" }
}
```

---

### 4.18 Order leaderboard — `GET /api/ops/order-leaderboard/`
Scope: `occ:read`. Honours the **general filter** (§3), on `completed_at`.

Riders ranked by **delivered-order volume** — `bottom_riders` = the lowest (including
zero-order riders), `top_riders` = the highest for context. `?top=20` sizes both lists.

**200 Response**
```json
{
  "success": true,
  "data": {
    "summary": { "riders_with_orders": 12, "riders_total": 25, "orders_delivered": 180 },
    "top_riders": [
      { "rider_id": "841149", "name": "Rider A", "delivered": 30, "gross_revenue": "15000.00" }
    ],
    "bottom_riders": [
      { "rider_id": "229883", "name": "Rider Z", "delivered": 0, "gross_revenue": "0.00" }
    ]
  },
  "date_range": { "filter": "this_month", "start": "…", "end": "…" }
}
```

---

### 4.19 Fuel misuse dashboard — `GET /api/ops/fuel-misuse-dashboard/`
Scope: `occ:read`. Honours the **general filter** (§3), on `FuelBill.bill_date`.

Riders who **collected fuel on a day** (from the daily fuel upload, §4.11) but **delivered fewer
than `min_orders`** orders that day (default **10** of **15** expected, from the `FUEL_MISUSE`
rule) — fuel spend with no matching output/revenue. One row per rider per fuel day.

**Query params**: `?min_orders=10`, `?expected_orders=15` (overrides).

**200 Response**
```json
{
  "success": true,
  "data": {
    "summary": {
      "min_orders": 10, "expected_orders": 15,
      "fuel_days": 14, "flagged_days": 3,
      "riders_fueled": 12, "riders_flagged": 3, "flagged_fuel_cost": "15400.00"
    },
    "rows": [ "…every rider×day fuel row, flagged first…" ],
    "flagged": [
      {
        "rider_id": "841149", "name": "Rider A", "date": "2026-07-03",
        "fuel_bills": 1, "fuel_cost": "5000.00", "liters": "4.200",
        "orders_delivered": 2, "orders_expected": 15, "min_orders": 10,
        "revenue": "3000.00", "flagged": true
      }
    ]
  },
  "date_range": { "filter": "this_month", "start": "…", "end": "…" }
}
```

---

## 5. Quick endpoint index

| Method | Path | Scope | Filter | Body |
|---|---|---|---|---|
| GET | `/api/ops/health/` | read | — | — |
| GET | `/api/ops/alerts/` | read | list filters | — |
| GET | `/api/ops/alerts/{id}/` | read | — | — |
| POST/PATCH | `/api/ops/alerts/{id}/resolve/` | write | — | status, resolution_note |
| POST | `/api/ops/alerts/generate/` | write | — | types? |
| GET | `/api/ops/alert-dashboard/` | read | §3 + limit | — |
| GET | `/api/ops/alert-rules/` | read | is_enabled? | — |
| GET/PUT/PATCH | `/api/ops/alert-rules/{id}/` | read/write | — | rule fields |
| GET | `/api/ops/order-dashboard/` | read | §3 | — |
| GET | `/api/ops/order-dashboard/orders/` | read | §3 + rider/merchant/order_status | — |
| GET | `/api/ops/tracking-dashboard/` | read | live (`limit`) | — |
| GET | `/api/ops/payments/` | read | §3 | — |
| GET | `/api/ops/payments/orders/` | read | §3 + method/payment_status/collection_timing | — |
| GET | `/api/ops/cod-dashboard/orders/` | read | §3 + rider/merchant/cod_status/order_status | — |
| GET | `/api/ops/cod-dashboard/` | read | §3 | — |
| POST | `/api/ops/fuel/upload/` | write | — | multipart `file` |
| GET | `/api/ops/fuel-dashboard/` | read | §3 | — |
| GET | `/api/ops/overriding-dashboard/` | read | §3 + allowance_km/top | — |
| GET | `/api/ops/attendance-dashboard/` | read | §3 + top | — |
| GET | `/api/ops/revenue-leaderboard/` | read | §3 + top | — |
| GET | `/api/ops/order-leaderboard/` | read | §3 + top | — |
| GET | `/api/ops/fuel-misuse-dashboard/` | read | §3 + min_orders/expected_orders | — |

---

## 6. Alert types (for `type` filter & rules)

`BIKE_AFTER_HOURS`, `GHOST_RIDE`, `RIDER_IDLE`, `SPEED_VIOLATION`, `LOW_ACCEPTANCE`,
`RIDER_INACTIVITY`, `LOW_CSAT`, `OVERRIDING`, `RIDER_OFFLINE_MOVING`, `LOW_REVENUE`,
`LOW_ORDER_VOLUME`, `FUEL_MISUSE`, `INCOMPLETE_ORDER`, `ORDER_STUCK`, `ORDER_DELAYED`,
`HIGH_CANCELLATION`, `RELAY_ROUTING_FAILURE`, `COD_RETENTION`, `COD_GAP`, `COD_FEE_LEAKAGE`,
`PAYMENT_FAILURE_SPIKE`, `HIGH_RIDER_PAYOUT`, `REVENUE_DROP`, `INSURANCE_EXPIRING`,
`REGISTRATION_EXPIRING`, `ROADWORTHINESS_EXPIRING`, `GPS_OFFLINE`, `SYNC_FAILURE`, `WEBHOOK_FAILURE`.

> Active evaluators today: `BIKE_AFTER_HOURS`, `INCOMPLETE_ORDER`, `GHOST_RIDE`, `SPEED_VIOLATION`,
> `GPS_OFFLINE`, `SYNC_FAILURE`, `ORDER_STUCK`, `ORDER_DELAYED`, `RELAY_ROUTING_FAILURE`,
> `COD_RETENTION`, `INSURANCE_/REGISTRATION_/ROADWORTHINESS_EXPIRING`, plus the rider-behaviour
> set: `OVERRIDING`, `RIDER_OFFLINE_MOVING`, `LOW_REVENUE`, `LOW_ORDER_VOLUME`, `FUEL_MISUSE`.
> The rest are defined (rules + dashboard counts) and will start firing as their evaluators are
> added — no contract change.

**Rider-behaviour rule defaults** (editable via `/api/ops/alert-rules/`):

| Type | Fires when | warn / crit | Key params |
|---|---|---|---|
| `OVERRIDING` | today's overriding km ≥ warn | 5 / 20 km | `allowance_km: 8` |
| `RIDER_OFFLINE_MOVING` | offline-moving km in 08:00–22:00 ≥ warn | 2 / 10 km | `day_start_hour: 8`, `day_end_hour: 22` |
| `LOW_REVENUE` | working rider's net revenue over 24h < warn | ₦5000 / ₦1000 | `window_minutes: 1440` |
| `LOW_ORDER_VOLUME` | working rider's delivered orders over 24h < warn | 5 / 2 | `window_minutes: 1440` |
| `FUEL_MISUSE` | fueled today but delivered < warn orders | 10 / 3 | `expected_orders: 15`, `evaluate_after_hour: 17` |

> "Working rider" = had a duty session, an assigned order, or a fuel bill in the window — riders
> who simply weren't rostered don't fire `LOW_REVENUE` / `LOW_ORDER_VOLUME`.
> `FUEL_MISUSE` only evaluates after 17:00 local so riders have the day to work.
