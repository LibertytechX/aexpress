# AXpress Alert Engine API — Frontend Guide

Everything the frontend needs to build the alert screens: the alert feed, the
alert dashboard, rule management, and the five rider-behaviour dashboards the
engine is built on (overriding, attendance, revenue, orders, fuel misuse).

**Base URL:** `https://orders.axpress.net/api/ops/`
**Auth:** currently disabled on all `/api/ops/` endpoints — no headers needed.
(When re-enabled it will be `Authorization: Bearer <service key>`.)

The engine runs automatically every **30 minutes** (Celery beat). It keeps
**one open alert per ongoing issue**: while a condition persists the same alert
is refreshed (`last_seen_at` moves forward), and when the condition clears the
alert **auto-resolves**. You can also trigger a run on demand (§2.4).

---

## 1. Conventions

### 1.1 Response envelope

Every endpoint returns:

```json
{
  "success": true,
  "data": { },
  "date_range": {
    "filter": "today",
    "start": "2026-07-03T00:00:00+01:00",
    "end": "2026-07-03T23:59:59.999999+01:00"
  }
}
```

`date_range` is `null` on endpoints that aren't date-filtered. Errors return
`{ "success": false, "detail": "..." }` with a 4xx/5xx status.

### 1.2 The general date filter

Date-filtered endpoints all accept the same `?filter=` param:

| `filter` | Extra params | Meaning |
|---|---|---|
| `today` | — | current local day |
| `this_week` | — | current week |
| `this_month` | — | current month (default when omitted) |
| `annually` | — | current year |
| `single_date` | `&date=YYYY-MM-DD` | one specific day |
| `date_range` | `&start_date=…&end_date=…` | inclusive custom range |

Example: `GET /api/ops/alert-dashboard/?filter=date_range&start_date=2026-07-01&end_date=2026-07-03`

### 1.3 Pagination (list endpoints)

`?page=1&page_size=25` (max 100). Paginated payloads include:

```json
{ "results": [ ], "count": 118, "page": 1, "page_size": 25, "total_pages": 5 }
```

### 1.4 Enums

- **severity**: `low` · `medium` · `high` · `critical`
- **status**: `new` · `investigating` · `resolved` · `false_positive`
  (open/active = `new` + `investigating`)
- **entity_type**: `rider` · `order` · `merchant` · `vehicle` · `zone` · `system`
- **alert_type**: see §5.

---

## 2. Alert endpoints

### 2.1 List alerts — `GET /alerts/`

The alert feed. Defaults to **active** (open) alerts only.

**Query params**

| Param | Values | Default |
|---|---|---|
| `status` | `active` (new+investigating) · `all` · any single status | `active` |
| `type` | an alert_type, e.g. `OVERRIDING` | — |
| `severity` | `low`/`medium`/`high`/`critical` | — |
| `entity_type` | `rider`/`order`/`vehicle`/… | — |
| `page`, `page_size` | pagination | 1, 25 |

**Sample** — `GET /api/ops/alerts/?type=OVERRIDING&severity=high`

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "9b6f0c9e-0d3a-4d6e-a2ab-1f2e3d4c5b6a",
        "alert_type": "OVERRIDING",
        "severity": "high",
        "entity_type": "rider",
        "title": "Overriding — 841149 +12.0 km over allowance",
        "description": "1 of 2 orders exceeded estimate + 8 km (actual 35.0 km vs allowed 31.0 km).",
        "value": "12.00",
        "context": {
          "rider_id": "841149",
          "date": "2026-07-03",
          "allowance_km": 8.0,
          "orders_checked": 2,
          "orders_over": 1,
          "total_estimated_km": 15.0,
          "total_allowed_km": 31.0,
          "total_actual_km": 35.0,
          "total_overriding_km": 12.0,
          "orders": [
            {
              "order_number": "AX10231",
              "completed_at": "2026-07-03T11:42:00+01:00",
              "estimated_km": 10.0,
              "allowed_km": 18.0,
              "actual_km": 30.0,
              "overriding_km": 12.0
            },
            {
              "order_number": "AX10240",
              "completed_at": "2026-07-03T13:05:00+01:00",
              "estimated_km": 5.0,
              "allowed_km": 13.0,
              "actual_km": 5.0,
              "overriding_km": 0.0
            }
          ]
        },
        "dedupe_key": "OVERRIDING:6a7b8c9d-…:2026-07-03",
        "status": "new",
        "resolution_note": "",
        "resolved_at": null,
        "first_seen_at": "2026-07-03T12:00:03+01:00",
        "last_seen_at": "2026-07-03T14:30:02+01:00",
        "created_at": "2026-07-03T12:00:03+01:00",
        "updated_at": "2026-07-03T14:30:02+01:00",
        "rider": "6a7b8c9d-1234-4bcd-9e8f-0a1b2c3d4e5f",
        "order": null,
        "merchant": null,
        "vehicle": "0f9e8d7c-4321-4dcb-8a9b-5f4e3d2c1b0a",
        "zone": null,
        "rider_code": "841149",
        "order_number": null,
        "vehicle_plate": "EPE440QS"
      }
    ],
    "count": 3,
    "page": 1,
    "page_size": 25,
    "total_pages": 1
  },
  "date_range": null
}
```

> **Display notes:** `title` is ready-made for the list row; `value` is the
> measured number that tripped the rule (km, ₦, order count — meaning depends
> on `alert_type`, see §5); `context` carries the type-specific detail for the
> expanded/detail view; `rider_code` / `order_number` / `vehicle_plate` are
> denormalized labels so you don't need extra lookups.

### 2.2 Alert detail — `GET /alerts/{id}/`

Same object shape as one `results[]` item above. **404** →
`{ "success": false, "detail": "Not found." }`.

### 2.3 Resolve / update status — `POST` or `PATCH /alerts/{id}/resolve/`

**Body**

```json
{ "status": "resolved", "resolution_note": "Spoke to rider, detour was a road closure." }
```

`status`: `resolved` (default) · `false_positive` · `investigating`.
Returns the updated alert object. **400** on any other status value.

### 2.4 Run the engine now — `POST /alerts/generate/`

**Body (optional):** `{ "types": ["OVERRIDING", "FUEL_MISUSE"] }` to limit the run.

```json
{
  "success": true,
  "data": {
    "evaluated": 18, "created": 4, "updated": 9, "resolved": 2,
    "skipped": 0, "no_evaluator": []
  },
  "date_range": null
}
```

### 2.5 Alert dashboard — `GET /alert-dashboard/`

Honours the **general filter** (§1.2). `?limit=20` caps `recent_active` (max 100).

```json
{
  "success": true,
  "data": {
    "period_summary": {
      "total": 42,
      "by_status": { "new": 9, "investigating": 3, "resolved": 28, "false_positive": 2 },
      "by_severity": { "critical": 5, "high": 14, "medium": 20, "low": 3 },
      "resolution_rate": 71.4
    },
    "period_by_type": [
      { "alert_type": "LOW_ORDER_VOLUME", "count": 11 },
      { "alert_type": "OVERRIDING", "count": 8 },
      { "alert_type": "FUEL_MISUSE", "count": 6 }
    ],
    "active": {
      "total": 12,
      "by_severity": { "critical": 2, "high": 6, "medium": 4, "low": 0 },
      "by_type": [
        { "alert_type": "OVERRIDING", "count": 4 },
        { "alert_type": "RIDER_OFFLINE_MOVING", "count": 3 }
      ]
    },
    "recent_active": [ "…up to `limit` full alert objects (§2.1 shape), newest last_seen first…" ]
  },
  "date_range": { "filter": "today", "start": "…", "end": "…" }
}
```

> `period_summary`/`period_by_type` = alerts **created in the period**.
> `active` = **currently open** alerts regardless of date (for the live counters).

### 2.6 List alert rules — `GET /alert-rules/`

`?is_enabled=true|false` to filter. Rules hold every threshold — nothing is
hardcoded, so an ops admin screen can tune the engine live.

```json
{
  "success": true,
  "data": [
    {
      "id": "3c2b1a09-…",
      "alert_type": "OVERRIDING",
      "is_enabled": true,
      "default_severity": "high",
      "warn_threshold": "5.00",
      "critical_threshold": "20.00",
      "window_minutes": null,
      "params": { "allowance_km": 8 },
      "description": "Delivered orders covered 5+ km (warn) / 20+ km (crit) beyond estimate + 8 km allowance today.",
      "updated_at": "2026-07-03T10:12:00+01:00"
    }
  ],
  "date_range": null
}
```

### 2.7 Get / edit one rule — `GET` / `PUT` / `PATCH /alert-rules/{id}/`

Editable fields: `is_enabled`, `default_severity`, `warn_threshold`,
`critical_threshold`, `window_minutes`, `params`, `description`
(`alert_type` is read-only). Example:

```json
PATCH /api/ops/alert-rules/3c2b1a09-…/
{ "warn_threshold": "10", "params": { "allowance_km": 10 } }
```

Returns the updated rule object.

---

## 3. Rider-behaviour dashboards

These power the drill-down screens behind the behaviour alerts. All honour the
**general filter** (§1.2), and all read their defaults from the matching
AlertRule so the dashboard and the engine always agree.

### 3.1 Overriding — `GET /overriding-dashboard/`

Per delivered order: **actual km** (vehicle GPS odometer delta between pickup
and completion) vs **allowed km** (saved order estimate + 8 km allowance).
The excess is overriding km, accumulated per rider with the per-order detail.

**Query params:** `?allowance_km=8` · `?top=10`

```json
{
  "success": true,
  "data": {
    "summary": {
      "allowance_km": 8.0,
      "orders_delivered": 40,
      "orders_checked": 36,
      "orders_no_estimate": 2,
      "orders_untracked": 2,
      "orders_with_overriding": 5,
      "riders_with_overriding": 3,
      "total_overriding_km": 41.5
    },
    "riders": [
      {
        "rider_pk": "6a7b8c9d-…",
        "rider_id": "841149",
        "name": "Ibrahim Musa",
        "plate_number": "EPE440QS",
        "orders_checked": 6,
        "orders_over": 2,
        "total_estimated_km": 51.0,
        "total_allowed_km": 99.0,
        "total_actual_km": 123.5,
        "total_overriding_km": 24.5,
        "orders": [
          {
            "order_number": "AX10231",
            "completed_at": "2026-07-03T11:42:00+01:00",
            "estimated_km": 10.0,
            "allowed_km": 18.0,
            "actual_km": 30.0,
            "overriding_km": 12.0
          }
        ]
      }
    ],
    "top_riders": [ "…the top N riders with total_overriding_km > 0, worst first…" ]
  },
  "date_range": { "filter": "today", "start": "…", "end": "…" }
}
```

> `riders` = every rider with checked orders (sorted worst-first) — use for the
> full table. `top_riders` = the top-10 card. `orders_untracked` /
> `orders_no_estimate` are orders that couldn't be scored (no GPS snapshots /
> no saved estimate) — show them as a data-quality hint, not as offences.

### 3.2 Attendance — `GET /attendance-dashboard/`

Per rider per day inside the **08:00–22:00 work window**: minutes online vs
offline (duty sessions) against the km the bike moved while online vs offline
(GPS). Offline movement = the `riders_offline_moving` flag. Ranges longer than
31 days are truncated to the most recent 31 (`days_truncated: true`).

**Query params:** `?top=10`

```json
{
  "success": true,
  "data": {
    "summary": {
      "work_window": "08:00–22:00",
      "days": 1,
      "days_truncated": false,
      "riders": 25,
      "riders_offline_moving": 2,
      "total_offline_moving_km": 12.4
    },
    "riders": [
      {
        "rider_pk": "6a7b8c9d-…",
        "rider_id": "841149",
        "name": "Ibrahim Musa",
        "plate_number": "EPE440QS",
        "status": "online",
        "online_minutes": 240,
        "offline_minutes": 600,
        "online_km": 10.0,
        "offline_moving_km": 7.0,
        "riders_offline_moving": true,
        "days": [
          {
            "date": "2026-07-03",
            "online_minutes": 240,
            "offline_minutes": 600,
            "online_km": 10.0,
            "offline_moving_km": 7.0
          }
        ]
      }
    ],
    "top_offline_moving": [ "…top N riders by offline_moving_km, worst first…" ]
  },
  "date_range": { "filter": "single_date", "date": "2026-07-03", "start": "…", "end": "…" }
}
```

> `riders` is sorted by `offline_moving_km` desc and includes clean riders
> (0 km offline) — use it for the full attendance table (hours online/offline
> per rider vs km moved). `days[]` only contains days with any activity.

### 3.3 Revenue leaderboard — `GET /revenue-leaderboard/`

Riders ranked by **net revenue** = gross delivered revenue − rider commission
(rate from SystemSettings, default 20%). `top_riders` = highest earners;
`bottom_riders` = lowest **including riders with zero revenue** in the window.

**Query params:** `?top=20` (sizes both lists)

```json
{
  "success": true,
  "data": {
    "summary": {
      "riders_with_revenue": 12,
      "riders_total": 25,
      "gross_revenue": "412000.00",
      "commission_total": "82400.00",
      "net_revenue": "329600.00",
      "commission_pct": "20"
    },
    "top_riders": [
      {
        "rider_id": "841149",
        "name": "Ibrahim Musa",
        "delivered": 30,
        "gross_revenue": "96500.00",
        "commission": "19300.00",
        "net_revenue": "77200.00"
      }
    ],
    "bottom_riders": [
      {
        "rider_id": "229883",
        "name": "Tunde Ade",
        "delivered": 0,
        "gross_revenue": "0.00",
        "commission": "0.00",
        "net_revenue": "0.00"
      }
    ]
  },
  "date_range": { "filter": "this_month", "start": "…", "end": "…" }
}
```

### 3.4 Order leaderboard — `GET /order-leaderboard/`

Riders ranked by **delivered-order volume**. `bottom_riders` = the lowest
(including zero-order riders) — the "top 20 riders with lower order" list;
`top_riders` = highest for context.

**Query params:** `?top=20`

```json
{
  "success": true,
  "data": {
    "summary": { "riders_with_orders": 12, "riders_total": 25, "orders_delivered": 180 },
    "top_riders": [
      { "rider_id": "841149", "name": "Ibrahim Musa", "delivered": 30, "gross_revenue": "96500.00" }
    ],
    "bottom_riders": [
      { "rider_id": "229883", "name": "Tunde Ade", "delivered": 0, "gross_revenue": "0.00" }
    ]
  },
  "date_range": { "filter": "this_month", "start": "…", "end": "…" }
}
```

### 3.5 Fuel misuse — `GET /fuel-misuse-dashboard/`

Cross-references the daily fuel upload with deliveries: riders who **collected
fuel on a day but delivered fewer than `min_orders`** (default 10 of 15
expected) that day. One row per rider per fuel day.

**Query params:** `?min_orders=10` · `?expected_orders=15`

```json
{
  "success": true,
  "data": {
    "summary": {
      "min_orders": 10,
      "expected_orders": 15,
      "fuel_days": 14,
      "flagged_days": 3,
      "riders_fueled": 12,
      "riders_flagged": 3,
      "flagged_fuel_cost": "15400.00"
    },
    "rows": [ "…every rider×day fuel row (same shape as below), flagged first…" ],
    "flagged": [
      {
        "rider_pk": "6a7b8c9d-…",
        "rider_id": "841149",
        "name": "Ibrahim Musa",
        "date": "2026-07-03",
        "fuel_bills": 1,
        "fuel_cost": "5000.00",
        "liters": "4.200",
        "orders_delivered": 2,
        "orders_expected": 15,
        "min_orders": 10,
        "revenue": "3000.00",
        "flagged": true
      }
    ]
  },
  "date_range": { "filter": "this_month", "start": "…", "end": "…" }
}
```

---

## 4. Quick endpoint index

| Method | Path | Date filter | Notes |
|---|---|---|---|
| GET | `/api/ops/alerts/` | — | `status`/`type`/`severity`/`entity_type` + pagination |
| GET | `/api/ops/alerts/{id}/` | — | single alert |
| POST/PATCH | `/api/ops/alerts/{id}/resolve/` | — | body: `status`, `resolution_note` |
| POST | `/api/ops/alerts/generate/` | — | body (opt): `types: []` |
| GET | `/api/ops/alert-dashboard/` | §1.2 | `?limit=` recent-active size |
| GET | `/api/ops/alert-rules/` | — | `?is_enabled=` |
| GET/PUT/PATCH | `/api/ops/alert-rules/{id}/` | — | edit thresholds/params |
| GET | `/api/ops/overriding-dashboard/` | §1.2 | `?allowance_km=` `?top=` |
| GET | `/api/ops/attendance-dashboard/` | §1.2 | `?top=` |
| GET | `/api/ops/revenue-leaderboard/` | §1.2 | `?top=` |
| GET | `/api/ops/order-leaderboard/` | §1.2 | `?top=` |
| GET | `/api/ops/fuel-misuse-dashboard/` | §1.2 | `?min_orders=` `?expected_orders=` |

---

## 5. Alert types the engine fires

For each type: what `value` means and what to expect inside `context`.

### 5.1 Rider behaviour (new set)

| Type | Fires when | `value` | Severity tiers (default) |
|---|---|---|---|
| `OVERRIDING` | today's accumulated overriding km ≥ 5 | overriding km | high / critical at 20 km |
| `RIDER_OFFLINE_MOVING` | bike moved ≥ 2 km while rider offline (08:00–22:00) | offline km | high / critical at 10 km |
| `LOW_REVENUE` | working rider's net revenue < ₦5000 over 24h | net ₦ | medium / critical at ≤ ₦1000 |
| `LOW_ORDER_VOLUME` | working rider delivered < 5 orders over 24h | delivered count | medium / critical at ≤ 2 |
| `FUEL_MISUSE` | fueled today, delivered < 10 of 15 expected (checked from 17:00) | delivered count | high / critical at ≤ 3 |

**Context payloads** (what to render in the detail view):

- `OVERRIDING`: `rider_id`, `date`, `allowance_km`, `orders_checked`,
  `orders_over`, `total_estimated_km`, `total_allowed_km`, `total_actual_km`,
  `total_overriding_km`, `orders[]` (per-order accumulation — see §2.1 sample).
- `RIDER_OFFLINE_MOVING`: `rider_id`, `date`, `plate_number`,
  `online_minutes`, `offline_minutes`, `online_km`, `offline_moving_km`,
  `days[]` (per-day split).
- `LOW_REVENUE`: `rider_id`, `window_minutes`, `delivered`, `gross_revenue`,
  `commission`, `net_revenue`.
- `LOW_ORDER_VOLUME`: `rider_id`, `window_minutes`, `delivered`,
  `gross_revenue`.
- `FUEL_MISUSE`: `rider_id`, `date`, `fuel_cost`, `liters`,
  `orders_delivered`, `orders_expected`, `min_orders`, `revenue`.

> "Working rider" for `LOW_REVENUE`/`LOW_ORDER_VOLUME` = had a duty session,
> an assigned order, or a fuel bill in the window. Riders who weren't rostered
> at all do **not** fire these.

### 5.2 Other active types

| Type | Fires when | `value` |
|---|---|---|
| `BIKE_AFTER_HOURS` | bike moving 20:00–06:00 | speed km/h |
| `GHOST_RIDE` | rider offline but assigned vehicle moving right now | speed km/h |
| `SPEED_VIOLATION` | speed ≥ 80 (high) / 120 (critical) km/h | speed km/h |
| `GPS_OFFLINE` | active vehicle, no telemetry ≥ 2h | minutes silent |
| `SYNC_FAILURE` | telemetry sync returned non-2xx | response code |
| `INCOMPLETE_ORDER` | accepted but not Done within 6h | hours since assigned |
| `ORDER_STUCK` | Pending/Assigned ≥ 4h | hours |
| `ORDER_DELAYED` | in transit ≥ 6h since pickup | hours |
| `RELAY_ROUTING_FAILURE` | relay order routing failed | — |
| `COD_RETENTION` | COD unremitted 24h+ (48h+ critical) | ₦ amount |
| `INSURANCE_/REGISTRATION_/ROADWORTHINESS_EXPIRING` | document expires ≤ 60d (30d critical) | days until expiry |

Defined but not yet firing (rules exist, evaluators pending — same contract):
`RIDER_IDLE`, `LOW_ACCEPTANCE`, `RIDER_INACTIVITY`, `LOW_CSAT`,
`HIGH_CANCELLATION`, `COD_GAP`, `COD_FEE_LEAKAGE`, `PAYMENT_FAILURE_SPIKE`,
`HIGH_RIDER_PAYOUT`, `REVENUE_DROP`, `WEBHOOK_FAILURE`.

---

## 6. Suggested screen mapping

- **Alerts inbox** → §2.1 list (tabs by `status`, chips by `severity`/`type`),
  row click → §2.2 detail, actions → §2.3 resolve.
- **Alert overview cards** → §2.5 dashboard (`active.by_severity` for the live
  counters, `period_summary` for the trend, `recent_active` for the ticker).
- **Rule settings screen** → §2.6/§2.7.
- **Overriding tab** → §3.1 (`top_riders` card + `riders` table, expand a row
  to show `orders[]` accumulation).
- **Attendance tab** → §3.2 (hours online/offline vs km, highlight
  `riders_offline_moving`).
- **Revenue / Orders tabs** → §3.3 + §3.4 (`top_riders` / `bottom_riders`).
- **Fuel misuse tab** → §3.5 (`flagged` list; `rows` for the full audit).
