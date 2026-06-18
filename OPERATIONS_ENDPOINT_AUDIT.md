# Operations Dashboard — Endpoint Accuracy Audit

> Running log of the COO-journey endpoint review. Goal: confirm each endpoint returns
> accurate data, does correct calculations, and uses no hardcoded / mock / guessed values.
> **No application code is changed during this exercise** — this file is documentation only.
>
> Reviewer context: logged in as **COO** → `scope.is_global = True` (sees all verticals/zones/riders).
> Date of review: 2026-06-18.
>
> **Findings below were verified against LIVE production data** via direct read-only API calls
> (base `https://www.orders.axpress.net`, COO account "Ayo", `/me/` → role `coo`, `is_global true`).
> Lines tagged **[LIVE ✓]** were confirmed with real responses, not inferred.

---

## Legend
- ✅ Verified correct / reconciles
- ⚠️ Works as coded, but semantics/product-intent questionable
- ❌ Confirmed bug / wrong or missing data
- 🔎 Needs product confirmation

---

## Page: Operations Dashboard (landing)

Endpoints observed in Network tab:
1. `GET /api/operations/v1/dashboard/summary/?period=this_month`
2. `GET /api/operations/v1/leaderboards/?period=this_month`
3. `GET /api/operations/v1/jumia-hubs/` (Jumia Hub Board — **not yet captured, pending**)

---

### 1. `GET /dashboard/summary/`
**Code:** `operations/services.py :: dashboard_summary()` → `order_metrics()`, `build_flags()`, `zone_target_values()`

**What it does:** Single roll-up for the header cards + flag counts for the selected period.

**Data pulled (all real, from DB):**
| Block | Source | Notes |
|---|---|---|
| `orders.*` | `Order` filtered by `created_at` in period, scoped by `rider__hub__zone` | global for COO |
| `riders.*` | `Rider` counts by `status` | point-in-time |
| `merchants.*` | `Merchant` counts by `activity_status` | see ❌ below |
| `targets.*` | `ZoneTarget` for the month | see ❌ below |
| `flags.*` | `build_flags()` computed at request time | see ❌ below |

**Calculations verified ✅**
- `completion_rate = completed/total*100` → 522/579 = 90.15 → **90.2** ✅
- `revenue` = Σ `total_amount` where `status="Done"` = **3,466,368** ✅
  - Reconciles exactly with the sum of the 4 zone revenues in the leaderboard (1,589,136 + 915,593 + 629,626 + 332,013 = 3,466,368) ✅
- `riders.total` 47 = online 35 + offline 12 ✅
- Header cards on screen reconcile: 522 completed ✅, ₦3.5M ✅, 0/204 active ✅, 29 flags ✅

**Findings**

❌ **F1 — All 204 merchants reported `inactive` (0 active / 0 watch). [LIVE ✓]**
`activity_status` is set by the scheduled task `dispatcher.tasks.update_merchant_activity_status` (every 6h, IS in `CELERY_BEAT_SCHEDULE`), which classifies on `Merchant.last_order_date`. **`last_order_date` is never updated by the real order flow** — only written by seed commands (`seed_occ_*`), so it holds stale seed values.
**Live proof:** of 204 merchants, only 52 have `last_order_date` set at all, and those values are months old. Merchant **"Adegold" has 90 orders this month but `last_order_date = 2026-02-22`** → classified `inactive`. "Nwagbaoso" 5 orders this month, `last_order_date = 2026-03-06` → `inactive`. 24 merchants have >0 orders this month; **all 24 are marked inactive.**
→ Root: `last_order_date` not bumped on order create/complete. The activity widget is wrong, not just empty.

❌ **F2 — Targets / attainment always 0.**
`targets.revenue = 0`, `revenue_attainment_pct = 0`, and the screen's **"OVERALL 0% This Month target"** all stem from there being **no `ZoneTarget` rows** for 2026-06. Not a calc bug — the target data simply isn't configured. 🔎 Confirm whether targets are expected to be seeded/entered via the admin endpoints (`admin/zone-targets/`).

❌ **F3 — KM integrity is 100% false positives; 0% pass rate. [LIVE ✓]**
`build_flags()` / `km_integrity()` flag when `|distance_today (GPS) − deliveries_km_today (order km)| / max(...) > 10%`.
**Live proof (`/km-visibility/`): of 41 vehicles, `deliveries_km_today > 0` for ZERO of them; `distance_today > 0` for 31. Result: passed = 0, failed = 31, available = 31.** Every vehicle that moved is flagged "failed". Example: AX-0039 GPS 13.94km vs order 0km → variance 100% → failed.
Root cause confirmed: `deliveries_km_today` is populated by the **management command `compute_deliveries_today`**, which is **NOT in `CELERY_BEAT_SCHEDULE`** (docstring says "run every 5 min via cron", but no beat entry / OS cron exists) → field stuck at 0 for all assets.
Secondary: even when run, it only sums orders **completed today** and skips the ~22% of completed orders with `distance_km = 0` (F10b), so the metric is fragile by design.
→ The headline **"29 anomalies / CRITICAL"** is not trustworthy — it is an artifact of a job that never runs.

⚠️ **F4 — `riders.on_delivery` is 0 everywhere** (summary and every zone). **[LIVE ✓ — still 0 for `period=today`]**
`Rider.Status.ON_DELIVERY = "on_delivery"` exists and is set via `start_delivery()`. Confirmed 0 at review time. It is point-in-time, so 0 may be legitimate, but combined with the fact that no rider was ever seen in this state, 🔎 verify the status is actually flipped during active deliveries (check a rider with an in-progress order).

🔎 **F5 — `orders_total` (579) > Σ zone order totals (560).**
The 19-order gap = orders whose rider has no hub/zone (or no rider). Completed counts and revenue still reconcile exactly, so the gap is non-completed/unassigned orders. Expected behavior, documented here so it isn't mistaken for a bug.

---

### 2. `GET /leaderboards/`
**Code:** `operations/services.py :: leaderboard()` → `zone_summary()`, `rider_summary()`, `vertical_summary()`

**What it does:** Ranks zones (by revenue), riders (by completed orders, top 50), verticals (by revenue).

**Calculations verified ✅**
- Zone `completion_rate`: Central 245/258 = 94.96 → **95** ✅; Southwest 92/106 = 86.79 → **86.8** ✅
- Zone ranks assigned by **revenue desc**: Central(1.58M) → North(916k) → Island(630k) → Southwest(332k) = ranks 1–4 ✅
- Rider ranks by `orders_completed` desc ✅

**Findings**

⚠️ **F6 — "Zone Leads" % shows `completion_rate`, but the badge is designed for target attainment. [FE CODE CONFIRMED]**
Confirmed in `DashboardPage.jsx:206`: `vPct = v.target_attainment_pct || (v.orders?.completion_rate) || v.pct || 0`. Because `target_attainment_pct` is **0** (F2/RC6) and the code uses `||` (0 is falsy), it **falls through to `completion_rate`**. `badge()`/`pc()` in `formatters.js` are explicitly commented *"based on attainment percentage"* — so a completion number is being rendered through an attainment-intended badge ("ON TRACK"). If targets existed, it would flip to attainment with no code change → unstable meaning. See FE-block for the `||` vs `??` inconsistency.

❌ **F7 — Zone cards are NOT fed by the leaderboard ranking at all. [FE CODE CONFIRMED]**
Earlier inference ("FE re-sorts by completion_rate") was wrong — the real mechanism:
- The cards render `zonesData` from **`useZones()` → `/zones/`**, which `order_by("name")` (alphabetical) and carries **no `rank`** field.
- `/leaderboards/` (which *does* return revenue rank) **is fetched but never used** — see **FE1**.
- `DashboardPage.jsx:102-108` sort: `if (a.rank && b.rank)` is false (no rank), then `pct = b.pct ?? b.target_attainment_pct ?? …` — with `??`, `target_attainment_pct=0` is non-nullish so it stops at **0 for every zone** → the sort is a no-op → alphabetical order remains.
- Result on screen: Central, **Island**, North, Southwest = **alphabetical**, not revenue rank. Confirmed mechanism, FE fix (use leaderboard rank or sort by revenue).

❌ **F8 — Zone-level merchant counts severely undercounted. [LIVE ✓]**
`zone_summary` does `Merchant.objects.filter(zone=zone)`. **Live proof: 151 of 204 merchants have NO zone assigned** (`zone.id = null`). `Merchant.zone` is only set by seed commands, not at signup/order time, so ~74% of merchants are invisible to any zone roll-up. (53 do have zones, so it's not 0 everywhere as first inferred — but the majority are unattributed.)

❌ **F9 — Test/admin accounts pollute the rider leaderboard.**
Ranks 23–29 include `Super Admin`, `Test Ignore`, `james Bond`, `Ali Ndume`, `Sulman Oguns`, `Inyang *`, etc. — 0-order accounts with `is_authorized=false`/no hub. `leaderboard()` uses `scoped_riders(scope)[:500]` with no filter for active/authorized/real riders. 🔎 Decide filter criteria (e.g. exclude unauthorized or hub-less riders, or those with 0 orders).

⚠️ **F10 — Revenue/distance inconsistency, correlated with order source. [LIVE ✓]**
Live check of 200 completed orders this month:
  - **F10a** — `total_amount` ranges ₦971 → ₦43,000 (median ₦3,170). The high-value orders are **`source = dispatcher_web`** (manually created: ₦27,000 / ₦33,000 / ₦26,000) and carry `distance_km = 0`; the normal `merchant_web` orders (₦3,837 / ₦1,675) have real distances. So per-order revenue is bimodal by source — `total_amount` is genuine revenue but dispatcher-entered orders use manual pricing with no distance. Not a bug per se, but it explains the leaderboard outliers (Collins ₦429k / Abdullahi ₦371k = clusters of dispatcher_web orders). 🔎 Confirm this is expected pricing behavior.
  - ❌ **F10b** — **44/200 completed orders have `distance_km = 0`; 45/200 have `duration = 0/null`** (~22%). These silently drag down `distance_km` totals and `avg_delivery_minutes`, and break F3's order-km basis. Distance/duration not captured on dispatcher-created completions.

⚠️ **F11 — `rating` is 0 for every rider.**
`rider_summary` averages `DeliveryRating.score` in period, falling back to `rider.rating` or 0. All zero → no `DeliveryRating` rows are being captured. 🔎 Confirm the rating pipeline is wired in prod.

**Reconciliation note:** zone revenue + completed totals reconcile perfectly with the summary (see F-block above), which gives good confidence the **core order aggregation (`order_metrics`) is correct**. The problems are in the *peripheral* data feeds (merchant attrs, KM, targets, ratings), not the order math.

---

---

## Page: Verticals  ( `/verticals/`, `/verticals/{id}/`, `/verticals/{id}/zones/` )
**Code:** `vertical_summary()` / `VerticalListView` / `VerticalDetailView` / `VerticalZonesView`

❌ **F12 — Entire vertical layer returns ZERO. [LIVE ✓]**
All 4 verticals (A Island & Lekki, B Central Mainland, C North & Ikorodu, D Southwest Mainland) report `zone_count: 0, rider_count: 0, orders_total: 0, revenue: 0`. `verticals/{id}/zones/` returns an empty `results`.
Root cause (see **RC6** below): `vertical_summary` gathers zones via `vertical.zones.filter(is_active=True)`, but **no active zone has its `vertical` FK set** — the 4 zones that actually carry traffic have `vertical = null`. So every vertical aggregates an empty zone set.
Net: vertical cards, vertical detail, and "zones under a vertical" are all dead until zone↔vertical links are fixed.
✅ `lead_name` is populated (from `VerticalLead`), so that part works.

---

## Page: Zones  ( `/zones/`, `/zones/{id}/`, `/zones/{id}/riders/` )
**Code:** `zone_summary()` / `ZoneListView` / `ZoneDetailView` / `ZoneRidersView`

✅ Order/rider aggregation per zone is correct and reconciles with the leaderboard.
✅ `zones/{id}/` includes nested `rider_list` (12 for Central Mainland) as the guide promises.
✅ `zones/{id}/riders/` returns `{period, zone_id, results}` with the same 12 riders.

❌ **F13 — Dashboard shows 4 zones; the system has 30. [LIVE ✓]**
`scoped_zones` filters `is_active=True`, so `/zones/` returns only the **4 active region-zones**. `admin/zones/` returns **30**. The other 26 (Agege, Ajah, Oshodi, Sabo, Ikorodu, …) are `is_active=False` — and those are the ones that carry verticals and targets (see RC6). So the operational zone list and the structural zone list are different sets that don't overlap.

⚠️ **F14 — `zone.vertical` is null on all 4 active zones**, so each zone's `vertical: {id:null,...}` block is empty in every zone/leaderboard payload. Same root as F12 (RC6).

---

## Page: Rider detail  ( `/riders/{id}/`, `/performance/`, `/daily-activity/`, `/vehicle/` )
**Code:** `RiderDetailView` / `RiderPerformanceView` / `RiderDailyActivityView` / `RiderVehicleView`

✅ `/riders/{id}/` returns correct real metrics (top rider: 76 total / 73 completed / 96.1% / ₦186,318 / 767.33 km).
✅ `/daily-activity/` returns one row **per calendar day** in the period (18 rows for Jun 1–18, 15 non-zero) with correct per-day metrics. Good.
✅ `/vehicle/` returns the assigned vehicle (KM status `failed` — same RC2 issue).

⚠️ **F15 — `/performance/` is byte-for-byte identical to `/{id}/`. [LIVE ✓]**
`RiderPerformanceView(RiderDetailView)` inherits with no override, so the "performance panel" gets the exact same payload as the profile drawer — no extra performance data (trend, rank, targets, on-time %, etc.). 🔎 Either enrich it or have the FE not call it twice.

⚠️ **F16 — `daily-activity` (fills every day) vs `orders/analytics.by_day` (only days with orders) are inconsistent.** Charts built off each will have different x-axes. Minor, but worth aligning.

---

## Page: Orders  ( `/orders/`, `/orders/analytics/` )
**Code:** `orders_list()` / `orders_analytics()`

✅ `/orders/analytics/` is solid: `by_status` (Done 522, CustomerCanceled 34, Failed 2, Pending 4, Assigned 14, Started 2, Arrived 1, AssignmentAccepted 1), `by_source` (merchant_web 467, dispatcher_web 113), `by_day` with per-day metrics. Summary reconciles (580 total / 522 completed).
✅ Order filters (`status`, `limit`) work — `status=Done` → count 522.

⚠️ **F17 — `/orders/` has no real pagination. [LIVE ✓]**
Returns `{count, results}` where `count` is the full count (580) but `results` is capped at `limit` (default 100, hard max 500 in `orders_list`). There is no offset/cursor, so a period with >500 orders **cannot be fully paged** from this endpoint. `last_month` already has 804 → only 500 reachable. 🔎 Add pagination or document the cap for the FE.

ℹ️ Confirms F10: 113/580 orders are `dispatcher_web` (manual pricing, frequent 0-distance).

---

## Page: Merchants  ( `/merchants/` )  — covered under F1/F8
✅ Filters (`activity_status`, `zone_id`, `is_partner`, `limit`) are wired.
❌ But see F1 (all inactive — stale `last_order_date`) and F8 (151/204 have no zone). `activity_status=active` will return **0 rows** in prod.

---

## Page: Jumia Hubs  ( `/jumia-hubs/` )
**Code:** `hubs_list()` / `hub_summary()` (reads `RelayNode`)

✅ Returns 24 hubs with `riders`, `orders`, zone, and `hub_captain_name/phone` populated. Aggregation correct.
⚠️ **F18 — 13/24 hubs have 0 orders this month. [LIVE ✓]** On the screen these render as **"0% / CRITICAL"**. A hub with no orders is *idle*, not *critical* — the FE is applying completion-rate thresholds to an empty hub. 🔎 Distinguish "no activity" from "poor performance" (same theme as F6).

---

## Page: Vehicles & KM  ( `/vehicles/`, `/km-visibility/`, `/km-integrity/` )
**Code:** `vehicles_list()` / `km_visibility()` / `km_integrity()` / `vehicle_summary()`

✅ `/vehicles/` returns 41 assets; `?status=active`→41, `?status=inactive`→0. Variance math (`km_variance_pct`) and status thresholds are coded correctly.
✅ `/km-integrity/?status=` filter works: failed 31, passed 0, unavailable 10 (= 41).
❌ But the data feeding it is broken — see **F3 / RC2**: `passed = 0` because `deliveries_km_today = 0` for all 41 vehicles. The endpoints are correct; the input data is not.

---

## Page: Admin console  ( `/admin/*` GET only — no writes performed )
✅ All admin GETs return 200 for COO: `admin/zones` 30, `admin/hubs` 25, `admin/zone-targets` 46, `admin/vertical-leads` 4, `admin/zone-captains` 23. Permission gating (`IsOperationsAdmin`) works.

❌ **F19 — Zone targets exist but are unusable for the live dashboard. [LIVE ✓]**
46 `ZoneTarget` rows exist, but: **(a)** every one is for **2026-02 or 2026-03** (none for the current month), and **(b)** **0 of them point at the 4 active zones** — they all target the 26 *inactive* zones (Agege, Ajah, …). So `zone_target_values(active_zone, current_month)` always finds nothing → targets/attainment = 0 everywhere (this is the real story behind F2 and the "OVERALL 0%" card).

---

## Period parsing  ( all endpoints )  [LIVE ✓]
✅ Verified end-to-end via `/dashboard/summary/`:
| period | range returned | orders |
|---|---|---|
| today | 06-18 → 06-18 | 3 |
| yesterday | 06-17 → 06-17 | 40 |
| this_week | 06-15(Mon) → now | 127 |
| past_7_days | 06-11 → now | 221 |
| this_month | 06-01 → now | 580 |
| last_month | 05-01 → 05-31 | 804 |
| this_year | 01-01 → now | 3190 |
| 2026-05 | 05-01 → 05-31 | 804 (= last_month ✓) |

⚠️ **F20 — Invalid periods fail silently to "current month".** `period=2026-13` and `period=garbage` both return the current-month range with no error (the `ValueError` is swallowed and falls through to the default). Per the guide an omitted period defaulting to this month is intended, but a *malformed* value silently returning different data than asked is a trap. 🔎 Consider 400-ing unknown values.

---

---

## Frontend ↔ API Consistency
> Source: `axpress-operations-command-center` repo, `frontend/` dir (React + Vite + axios + react-query),
> cloned read-only to `operations-frontend/` (git-ignored). Findings cite exact files/lines.
> The API wrapper layer (`src/api/endpoints.js`) maps **1:1** to the backend — good. Issues are in
> render/transform logic and in endpoints the FE expects but the backend doesn't expose.

❌ **FE1 — `/leaderboards/` is fetched on every dashboard load and never used. [CODE CONFIRMED]**
`DashboardPage.jsx:63` calls `useLeaderboards()` but `leaderboardData` is referenced nowhere else. It's a wasted request **and** the root of F7 — the correctly-ranked data is fetched then discarded while the cards use the alphabetical `/zones/` list. Fix: either drop the call or use it to drive the zone cards (which also fixes F7).

❌ **FE2 — Merchant cards read fields the operations API never returns. [CODE + LIVE CONFIRMED]**
`formatters.js:calcMerchantStats` and `HubPage.jsx` / `CommTab.jsx` read `m.status`, `m.orders_placed`, `m.gross_revenue`, `m.avg_order_value`, `m.fulfillment_rate`. The operations `merchant_summary` returns **`activity_status`** (not `status`), nested **`orders.{orders_total,revenue}`** (not `orders_placed`/`gross_revenue`), and has **no** `avg_order_value` / `fulfillment_rate`. Net: merchant revenue/orders render as **0**, status filters (`m.status === "active"`) match **nothing**, and avg-order/fulfillment show 0%. (These are FE bugs independent of the F1 backend data gap — even once F1 is fixed, the FE would still read the wrong keys.)

❌ **FE3 — "APEX Coach" and "Comms" features call endpoints that don't exist (404). [LIVE CONFIRMED]**
`endpoints.js` defines `coach/chat/`, `comms/templates/`, `comms/broadcasts/`, `comms/notifications/` under `/operations/v1/`. None are in the backend `operations/urls.py`, and live calls return **HTTP 404** for all four. So the entire Coach + Comms surface is broken end-to-end — the backend operations app never implemented these routes. 🔎 Decide whether these are planned backend work or should be removed from the FE.

⚠️ **F18 (mechanism confirmed) — idle hubs show "CRITICAL".**
`DashboardPage.jsx:288,324`: `zPct = z.orders?.completion_rate ?? … ?? 0` → `badge(zPct)`. A 0-order hub has `completion_rate = 0` → `badge(0)` → "CRITICAL" (`formatters.js:24`). Confirmed: idle ≠ failing, but the FE renders them identically.

⚠️ **FE4 — `||` vs `??` used inconsistently for the same metric.**
Zone **display** (`:206`) uses `||` (skips 0 → shows completion_rate); zone **sort** (`:105`) uses `??` (keeps 0 → all equal). So the same zone is treated as "0%" for ordering but "95%" for the badge in one render. Pick one nullish strategy.

✅ **FE-OK** — KPI header cards (`:81-99`) map correctly to `summary.orders/merchants/flags/targets`; `fmt()` currency (₦1.6M) and `fmtN()` match the screen. Period context is passed consistently to all hooks.

---

## Per-screen frontend audit (API-driven)
> Method: for each operations endpoint, find every call site (via `useApi.js` hooks) and diff the
> component's field access against the **actual** API response shape (confirmed live). **Pattern that
> recurs everywhere → RC7:** the FE was built against an *assumed* contract (flat field names +
> `total_*`/`*_breakdown` aliases) that does not match the backend (nested objects + `summary.*`,
> `by_status`, `total_amount`, etc.). **Every mismatch has a hardcoded mock fallback**, so instead of
> showing 0/blank, the UI renders **plausible fake numbers**. This is the "mock/hardcoded values"
> risk the audit was commissioned to find.

### Screen: Orders  (`OrdersPage.jsx`) — endpoints `/orders/`, `/orders/analytics/`, `/zones/`
❌ **FE5 — Analytics cards & charts are hardcoded mock values. [CODE CONFIRMED]**
The component reads fields the analytics API never returns; each falls back to a literal:
| UI element | FE reads | API actually returns | Renders |
|---|---|---|---|
| Total Volume | `analytics.total_orders` | `summary.orders_total` | falls back to `orders.length` (page rows, ≤limit) |
| Revenue | `analytics.total_revenue` | `summary.revenue` | **₦0** always |
| Avg Delivery time | `analytics.avg_delivery_mins` | `summary.avg_delivery_minutes` | **hardcoded "28" mins** |
| Fulfillment Rate | `analytics.fulfillment_rate` | `summary.completion_rate` | **hardcoded "94.5%"** |
| Status Share chart | `analytics.status_breakdown` (obj of %) | `by_status` (array of `{status,count}`) | **hardcoded `{Delivered:85, In Transit:10, Pending:5}`** |
| Channel chart | `analytics.channel_breakdown` | `by_source` | **hardcoded `{Merchant App:60, Jumia Relay:30, Phone Dispatch:10}`** |

❌ **FE5b — Orders table: 4 of 7 columns blank/zero. [CODE CONFIRMED]**
`o.zone_name` (API: `zone.name`), `o.merchant_name` (API: `merchant.name`), `o.rider_name` (API: `rider.name`) → all render **"—"**; `o.amount || o.revenue` (API: `total_amount`) → **₦0**. Only Order ID (id slice — should be `order_number`), Date, and Status are correct.
⚠️ **FE5c** — Status filter `<option>`s (`Processing`, `Transit`, `Cancelled`) don't match backend statuses (`Started`, `CustomerCanceled`, …) → those filters return nothing.

### Screen: Vehicles & KM  (`VehiclesPage.jsx`) — endpoints `/vehicles/`, `/km-visibility/`, `/km-integrity/`
❌ **FE6 — KM banner shows fake healthy numbers that contradict reality. [CODE CONFIRMED]**
| UI element | FE reads | API returns | Renders | Reality |
|---|---|---|---|---|
| Audit Pass Rate | `visibility.pass_rate` | `passed`/`count` (no `pass_rate`) | **hardcoded "91.2%"** | actual pass rate **0%** |
| Critical Variance | `visibility.failed_count` | `failed` (=31) | **hardcoded "3"** | actual **31** |
| Odometer Tracked | `visibility.total_distance_km` | (none) | "—" | — |
| Fleet Count | `visibility.total_vehicles` | `count` | falls back to `vehicles.length` (41 ✓) | ok by accident |
This is the most dangerous screen: it renders **91.2% pass / 3 failures** while the system is actually **0% pass / 31 failures** (RC2). A reader would conclude KM integrity is healthy.

❌ **FE6b — Telemetry & integrity tables read wrong keys. [CODE CONFIRMED]**
- Telemetry: `v.assignment` (API: `assigned_rider.name`) → "Unassigned" always; `v.telemetry_location` (API: `location`) → "No GPS Lock" always.
- Integrity: `log.variance` (API: `km_variance_pct`) → **"—"** always; `log.status` (API: `km_integrity_status`) → badge **"UNAVAILABLE"** for every row (and color logic keyed off the wrong field). So even the rows the backend returns as `failed` display as "UNAVAILABLE" with no variance.

### Screen: Rider detail  (`RiderPage.jsx`) — endpoints `/riders/{id}/`, `/performance/`, `/daily-activity/`, `/vehicle/`
⚠️ **FE7 — Hero numbers inconsistent + most performance metrics empty with hardcoded targets. [CODE CONFIRMED]**
- The derived block (`:77-82`) reads nested `stats.orders.*` correctly, but the **hero stat row** (`:131-132`) reads **flat** `stats.orders_completed` / `stats.revenue` → both render **0 / ₦0** even though the data exists. Same value shown two ways.
- **6 of 9 "Performance Metrics" and all 5 gauges are empty** because the FE expects a rich `performance` payload the backend doesn't provide (ties to **F15** — `/performance/` == `/{id}/`): `rev_per_km`, `online_days`, `ghost_ratio`, `csat_avg`, `peak_util`, `acceptance_rate` (flat) → all `0`/`"—"`; their **targets are hardcoded literals** ("₦3,333/km", "22d", "92%", "<8%", "28m", "4.5★", "75%").
- `avg_delivery_minutes` IS returned by the API but the FE reads flat `stats.avg_delivery_mins` (wrong path) → "—".
- `rider.hub_name` (API: `hub.name`) → falls back to literal "Hub"/"Assigned Hub".
- ✅ Works: daily-activity chart (`row.orders_completed`/`row.revenue`/`row.date`), and the vehicle panel (uses correct `km_integrity_status`/`deliveries_km_today` fallbacks — except `telemetry_location` → "No GPS Lock").

### Screen: Zone detail  (`ZonePage.jsx`) — `/zones/{id}/`, `/zones/{id}/riders/`, `/merchants/?zone_id`, `/jumia-hubs/`
❌ **FE8 — "Lead Earnings" panel is fully fabricated on the client. [CODE CONFIRMED]**
`:80-81` invents `commission = total_revenue * 0.011` and `lead_pay = commission / 0.06`, then `:191` splits it into "Base Pay" (×0.75), "Transport" (×0.19), "Commission" (×0.06). **None of this comes from the backend** — there is no payroll/commission endpoint. The COO sees a precise-looking lead salary breakdown that is a pure arithmetic artifact of revenue. (HubPage has the identical "Captain Earnings" fabrication: `zoneRevenue*0.011/0.06`, split 0.7/0.2/0.1.)
- Hero % uses the F6 `||`-on-zero pattern (shows completion_rate).
- ✅ Works: order totals, revenue, avg delay, avg distance, rider-health buckets (all read nested `orders.*` / `riders.*`).
- ❌ Merchant Health + Merchants tab broken via **FE2** (`m.status`/`orders_placed`/`merchant_type`/`hub_name`); ❌ Ghost-ride alerts read non-existent `r.ghost_ratio` → always "None flagged ✓" (false reassurance).

### Screen: Hub detail  (`HubPage.jsx`) — `/jumia-hubs/`, `/zones/{id}/...`, `/merchants/?zone_id`
❌ **FE9 — "Captain Earnings" fabricated (as above); "On Track" KPI always 0. [CODE CONFIRMED]**
- Hero "On Track" (`:128`) filters `r.pct >= 70`, but riders have no `.pct` (it's `orders.completion_rate`) → **always 0/N**.
- Recomputes hub performance from rider sums instead of using the `hub.orders.*` the jumia-hubs API already returns.
- Merchant cards read `gross_revenue`/`avg_order_value`/`fulfillment_rate`/`orders_placed`/`status` → all **₦0 / 0% / blank** (FE2); merchant sort keys are all `undefined` → no-op.
- ✅ Works: rider list rows (nested `orders.*`), hub name from jumia-hubs.

### Screen: Admin console  (`AdminPage.jsx`) — `/admin/*`
✅ **Healthiest screen.** Straight CRUD against the real admin endpoints; zone-target form correctly normalizes `month` to first-of-month and coerces `target_orders`/`target_revenue`; zone form exposes `vertical` + `zone_lead`. **This is the surface where the COO can actually fix RC6** (link active zones to verticals, create current-month targets).
🔎 **FE10 (verify)** — the vertical-lead / zone-captain assign forms need a **user picker**, but there's no user-list endpoint in `endpoints.js`; confirm how the `user` UUID is sourced (may be manual entry or a missing endpoint).

---

## Cross-cutting root causes (recurring)
| ID | Root cause | Impacts |
|---|---|---|
| RC1 | `Merchant.last_order_date` & `Merchant.zone` not maintained by prod order flow (only seeds) | F1, F8, merchant widgets, zone merchant counts |
| RC2 | `compute_deliveries_today` not in `CELERY_BEAT_SCHEDULE` → `deliveries_km_today` stuck at 0 | F3 (all KM-integrity flags), vehicle KM variance |
| RC3 | Targets (`ZoneTarget`) not configured for current month | F2, F6, OVERALL card |
| RC4 | Order records missing `distance_km` / `duration_minutes` on completion | F3, F10b, avg delivery time, distance totals |
| RC5 | No quality filter on riders surfaced to operations views | F9 |
| **RC7** | **Frontend built to an assumed contract + hardcoded fallbacks.** Many components read field names the operations API never returns (`total_orders`/`total_revenue`/`status_breakdown`, flat `zone_name`/`merchant_name`/`amount`, `pass_rate`/`failed_count`, `m.status`/`gross_revenue`, rich rider-performance fields). Each miss falls back to a literal (28 mins, 94.5%, 91.2%, "3", fake chart %), so the UI shows **plausible fake numbers instead of blanks**. Two panels (Lead/Captain Earnings) are **fully fabricated** from `revenue × 1.1% ÷ 6%`. | **FE5, FE6, FE7, FE8, FE9** — Orders analytics, KM banner, rider metrics, lead/captain pay |
| **RC6** | **Two disconnected zone hierarchies.** 4 `is_active=True` "region" zones (Central Mainland, Island & Lekki, North & Ikorodu, Southwest Mainland) carry ALL riders/hubs/orders but have `vertical=null` and no targets. 26 `is_active=False` "area" zones (Agege, Ajah, Oshodi, …) carry the vertical links (23) and all 46 targets, but have no traffic. The metrics layer reads the active set; the structural layer (verticals, targets) reads the inactive set. **They never intersect.** | **F2, F6, F12, F13, F14, F19** — vertical rollups all 0, all target attainment 0 |

## Confirmed correct (no action)
- Order aggregation math: completion rate, revenue sum, totals — all reconcile across summary↔leaderboard.
- Period parsing for `this_month` (`2026-06-01` → now). ✅
- Scope = global for COO. ✅

---

## Endpoints reviewed
- [x] `me/`
- [x] `dashboard/summary/`
- [x] `dashboard/flags/` + `flags/` (alias — identical; all 29 are `km_integrity` criticals, see F3)
- [x] `leaderboards/`
- [x] `verticals/`, `verticals/{id}/`, `verticals/{id}/zones/`
- [x] `zones/`, `zones/{id}/`, `zones/{id}/riders/`
- [x] `riders/{id}/`, `riders/{id}/performance/`, `riders/{id}/daily-activity/`, `riders/{id}/vehicle/`
- [x] `orders/`, `orders/analytics/`
- [x] `merchants/`
- [x] `jumia-hubs/`
- [x] `vehicles/` (+ status filters)
- [x] `km-visibility/`, `km-integrity/` (+ status filters)
- [x] `admin/*` (GET only — no writes performed against prod)
- [x] period parsing (all 8 supported values + invalid handling)

## Fix Ownership Classification

> Split by where the fix actually lives. **Category 1** = inside the operations app
> (`backend/operations/` — you own this end to end). **Category 2** = outside the operations app
> (needs the wider team / other Django apps / infra / data decisions / frontend).

### Category 1 — Fixable inside the operations app (you, solo)
These are pure `backend/operations/` code changes; no other team needed.

| # | Finding | Fix (in operations app) |
|---|---|---|
| F9 | Test/admin riders pollute leaderboard | In `leaderboard()` / `scoped_riders()`, filter out unauthorized / hub-less / 0-order accounts before ranking. |
| F15 | `/riders/{id}/performance/` duplicates `/{id}/` | Give `RiderPerformanceView` its own richer payload (trend, rank, on-time %), or drop the route. |
| F16 | `analytics.by_day` skips zero-order days while `daily-activity` fills them | Make `orders_analytics.by_day` iterate every day in the range (mirror `rider_daily_activity`). |
| F17 | `/orders/` has no pagination (hard 500 cap) | Add offset/cursor paging to `orders_list()`, or document the cap explicitly. |
| F20 | Invalid `period` silently returns current month | In `parse_period()`, raise 400 on malformed values instead of swallowing `ValueError`. |

### Category 1b — Operations app can *mitigate*, but the real fix is external
You can ship a workaround in operations code, but the clean fix lives elsewhere (see Cat. 2).

| # | Finding | Operations-app mitigation | Real fix |
|---|---|---|---|
| F1 | Merchants all `inactive` | Compute activity live from `Order` rows inside operations (ignore stale `activity_status`) | RC1 — maintain `last_order_date` (Cat. 2) |
| F12/F14/F19 | Verticals & targets dead (RC6) | Use your own `admin/zones` PATCH to set `vertical`, and `admin/zone-targets` POST to create current-month targets on the **active** zones | Resolve the dual-hierarchy at the data layer (Cat. 2) |

### Category 2 — Needs the wider team (outside the operations app)

**2a — Data / structural decisions (RC6)** — *you can enter data via your admin endpoints, but the team must decide the canonical model*
| # | Finding | Who / where |
|---|---|---|
| F12/F13/F14 | 4 active "region" zones carry traffic but have no vertical link; 26 structured zones are inactive | Decide which zone hierarchy is canonical, then either set `vertical` on the active zones **or** migrate riders/hubs onto the structured zones. Touches dispatch/zone ownership. |
| F2/F19 | All 46 targets are on inactive zones, for Feb/Mar only | Re-create targets against the active zones for the live month (data entry + ownership of who sets targets). |

**2b — Other backend apps / infra (not `operations/`)**
| # | Finding | Where the fix lives |
|---|---|---|
| F3 (RC2) | KM integrity 100% false — `compute_deliveries_today` never runs | Add it to `CELERY_BEAT_SCHEDULE` (settings) / infra cron. Owned by core backend/devops. |
| F1/F8 (RC1) | `last_order_date` & `merchant.zone` never set in prod | `orders` create/complete flow + merchant onboarding. Core backend. |
| F4 | `rider.on_delivery` never set | Dispatch/assignment flow must call `start_delivery()` / flip status. Core backend. |
| F10b (RC4) | ~22% of completed orders missing `distance_km`/`duration` (dispatcher_web) | Order completion logic for dispatcher-created orders. Core backend. |
| F11 | All rider ratings 0 | `DeliveryRating` capture pipeline. Core backend. |
| F10a | `total_amount` semantics differ by source | Product/pricing clarification. |

**2c — Frontend (the dashboard UI repo, not the operations API)** — *fixes live in `axpress-operations-command-center/frontend`*
| # | Finding | Where the fix lives |
|---|---|---|
| F6 / FE4 | Zone % shows `completion_rate` through an attainment badge; `\|\|` vs `??` inconsistency | `DashboardPage.jsx:105,206` — pick one nullish strategy; decide completion vs attainment with product. |
| F7 / FE1 | Zone cards use alphabetical `/zones/`; `/leaderboards/` fetched but unused | `DashboardPage.jsx:63,102` — drive cards from leaderboard rank (or sort by revenue) and drop the dead fetch. |
| FE2 | Merchant cards read non-existent fields (`status`, `gross_revenue`, `orders_placed`, `avg_order_value`, `fulfillment_rate`) → render 0/blank | `formatters.js:calcMerchantStats`, `HubPage.jsx`, `CommTab.jsx` — map to `activity_status` + nested `orders.*`. |
| F18 | Idle (0-order) hubs rendered as "CRITICAL" | `DashboardPage.jsx:288,324` — distinguish "no activity" from "poor performance". |
| **FE5** | Orders analytics cards/charts = hardcoded mocks (28m, 94.5%, 85/10/5, 60/30/10); table cols blank/₦0 | `OrdersPage.jsx` — map `summary.*`, `by_status`, `by_source`, nested `zone/merchant/rider`, `total_amount`. |
| **FE6** | KM banner shows fake **91.2% pass / 3 failed** while reality is **0% / 31** | `VehiclesPage.jsx` — map `passed`/`failed`/`count`; fix `km_variance_pct`, `km_integrity_status`, `assigned_rider`, `location`. |
| **FE7** | Rider: 6/9 metrics + all gauges empty w/ hardcoded targets; hero 0/₦0 | `RiderPage.jsx` — read nested `orders.*`; needs richer `/performance/` (F15) for the rest. |
| **FE8 / FE9** | **Fabricated Lead/Captain Earnings** (`revenue×1.1%÷6%`); merchant fields all 0; "On Track" always 0 | `ZonePage.jsx`, `HubPage.jsx` — remove fabricated payroll or back it with a real endpoint; fix FE2 merchant fields; use `orders.completion_rate` not `r.pct`. |

**2d — FE/backend contract gap**
| # | Finding | Decision needed |
|---|---|---|
| FE3 | FE calls `/operations/v1/coach/chat/` + `/comms/*` → **404** (routes never built) | Either **build them in the operations app** (this *would* be Category-1 backend work you own) **or** remove the Coach/Comms surface from the FE. Product call. |

### One-line summary for the team conversation
- **You can fix solo (Cat. 1):** F9, F15, F16, F17, F20 — and *mitigate* F1 + RC6 from inside operations.
- **Frontend repo (Cat. 2c):** F6/F7/F18 + FE1 (dead leaderboard fetch), FE2 (merchant field mismatches → 0s), FE4 (`\|\|`/`??`). These are independent of the backend and can ship in parallel.
- **Contract gap (Cat. 2d):** FE3 — Coach/Comms call 404 routes; build in operations app or remove from FE.
- **Needs the team (Cat. 2a/2b):** the two that unlock the most dashboard are **RC2** (schedule `compute_deliveries_today` → fixes KM + all flags) and **RC6** (link active zones to verticals + set current-month targets → fixes verticals, targets, attainment). Then RC1 (merchant activity), F4, F10b, F11 are core-backend data-capture gaps.

### Biggest frontend takeaway (RC7)
The dashboard's **numbers cannot be trusted at face value** — not because the API is wrong (it's mostly right), but because the FE reads the wrong keys and **falls back to hardcoded mock values**, so screens render plausible fakes. Worst offenders: the **KM banner (91.2% pass / 3 failed vs. real 0% / 31)** and the **fabricated Lead/Captain Earnings** panels. The fix is mechanical (correct field mapping) but broad — it touches every page except Admin.

### Coverage
- **Backend:** all operations endpoints (live, read-only as COO). ✅ complete.
- **Frontend:** API layer + hooks, and **every consuming screen** — Dashboard, Orders, Vehicles/KM, Rider, Zone, Hub, Admin (`axpress-operations-command-center/frontend`, read-only clone). ✅ complete.
- Not audited: `auth/*`, `layout/*`, `shared/*` chart primitives, `coach/*` (dead — FE3). No production writes; no app code changed.

---

## Note on method
All findings verified read-only against `https://www.orders.axpress.net` as COO ("Ayo").
No write/POST/PATCH/PUT calls were made against production. No application code was modified.
