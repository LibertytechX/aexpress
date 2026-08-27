# Operations Dashboard API Guide

## Purpose

This guide is for the frontend developer building the new Assured Express Operations Dashboard.

The frontend should use the new API namespace only:

```text
/api/operations/v1/
```

Do not use the legacy `/api/occ/` endpoints for the new dashboard.

## Important Product Constraint

This dashboard uses the existing backend system only.

No new models are being introduced for the dashboard. If a business concept does not already have reliable data in the current system, the frontend should not display it as a real metric.

Currently unavailable as first-class dashboard data:

- Hire-purchase lease agreements
- Lease payment history
- Missed lease payment reconciliation
- Persisted KM integrity audit records
- GPS daily KM ingestion records

The backend may expose computed KM visibility from existing `VehicleAsset` fields, but it does not store new KM integrity records for this dashboard.

## Authentication

All endpoints require authentication.

Use the existing backend auth mechanism:

```http
Authorization: Bearer <access_token>
```

The backend determines dashboard scope from the authenticated user.

## Role Scoping

The frontend should not manually enforce operational scope. The API already scopes responses.

Supported scopes:

- `coo`: full business visibility.
- `vertical_lead`: assigned vertical and zones under that vertical.
- `zone_captain`: assigned zone only.
- `service`: service-key access, full visibility.
- `unknown`: authenticated user without an operational scope.

Call this endpoint after login:

```http
GET /api/operations/v1/me/
```

Use it to configure available navigation and filters.

Example response:

```json
{
  "id": "user-uuid",
  "name": "Ops Manager",
  "role": "coo",
  "is_global": true,
  "vertical_ids": [],
  "zone_ids": [],
  "permissions": {
    "can_view_all": true,
    "can_view_km_integrity": true
  }
}
```

## Period Filters

Dashboard endpoints that support time filtering accept:

```text
?period=<value>
```

Current supported values:

- `today`
- `yesterday`
- `this_week`
- `past_7_days`
- `this_month`
- `last_month`
- `this_year`
- `YYYY-MM`

Month dropdown mapping:

```text
Jan -> period=2026-01
Feb -> period=2026-02
Mar -> period=2026-03
Apr -> period=2026-04
May -> period=2026-05
Jun -> period=2026-06
Jul -> period=2026-07
Aug -> period=2026-08
Sep -> period=2026-09
Oct -> period=2026-10
Nov -> period=2026-11
Dec -> period=2026-12
```

If `period` is omitted, the backend defaults to the current month.

## Common Response Patterns

List endpoints usually return:

```json
{
  "period": "this_month",
  "count": 10,
  "results": []
}
```

Some dashboard aggregate endpoints return a single object instead of `results`.

Errors use the existing DRF style:

```json
{
  "detail": "Authentication credentials were not provided."
}
```

or:

```json
{
  "detail": "You do not have access to this zone."
}
```

## Endpoint List

### Current User

```http
GET /api/operations/v1/me/
```

Returns authenticated user identity, role, scope, and dashboard permissions.

Use this before rendering the dashboard shell.

### Dashboard Summary

```http
GET /api/operations/v1/dashboard/summary/?period=this_month
```

Returns high-level KPIs:

- orders
- revenue
- rider counts
- merchant counts
- target revenue attainment where targets exist
- computed flag counts

Use this for the top dashboard cards.

### Dashboard Flags

```http
GET /api/operations/v1/dashboard/flags/?limit=50
GET /api/operations/v1/flags/?limit=50
```

Returns computed operational flags from existing fields.

Current flag sources:

- Rider is offline but current speed indicates movement.
- Vehicle GPS KM and completed-order KM differ by more than 10%.

These are computed at request time. They are not persisted records.

### Verticals

```http
GET /api/operations/v1/verticals/?period=this_month
GET /api/operations/v1/verticals/{vertical_id}/?period=this_month
GET /api/operations/v1/verticals/{vertical_id}/zones/?period=this_month
```

Use these for:

- vertical cards
- vertical detail page
- zones under a selected vertical

The API scopes the list based on the current user.

### Zones

```http
GET /api/operations/v1/zones/?period=this_month
GET /api/operations/v1/zones/{zone_id}/?period=this_month
GET /api/operations/v1/zones/{zone_id}/riders/?period=this_month
```

Use these for:

- zone table
- zone performance page
- rider list inside a zone

Zone detail includes nested rider summaries.

### Riders

```http
GET /api/operations/v1/riders/{rider_id}/?period=this_month
GET /api/operations/v1/riders/{rider_id}/performance/?period=this_month
GET /api/operations/v1/riders/{rider_id}/daily-activity/?period=this_month
GET /api/operations/v1/riders/{rider_id}/vehicle/
```

Use these for:

- rider profile drawer/page
- performance panel
- day-by-day activity chart
- vehicle assignment panel

### Leaderboards

```http
GET /api/operations/v1/leaderboards/?period=this_month
```

Returns rankings for:

- zones
- riders
- verticals

Current ranking logic:

- zones and verticals rank by revenue
- riders rank by completed orders

### Orders

```http
GET /api/operations/v1/orders/?period=this_month
GET /api/operations/v1/orders/analytics/?period=this_month
```

Supported filters for order list:

```text
status=Done
zone_id=<uuid>
rider_id=<uuid>
merchant_id=<user_uuid>
limit=100
```

Use `/orders/` for an operational order table.

Use `/orders/analytics/` for status/source/day trend charts.

### Merchants

```http
GET /api/operations/v1/merchants/?period=this_month
```

Supported filters:

```text
zone_id=<uuid>
activity_status=active|watch|inactive
status=active|watch|inactive
is_partner=true|false
limit=100
```

Use this for merchant visibility by zone and activity state.

### Jumia Hubs

```http
GET /api/operations/v1/jumia-hubs/?period=this_month
```

Supported filters:

```text
zone_id=<uuid>
```

This endpoint uses existing `RelayNode` records. It does not create a separate Jumia hub model.

Use this for:

- hub list
- assigned rider counts
- hub-to-zone visibility
- hub order rollups

### Vehicles

```http
GET /api/operations/v1/vehicles/
GET /api/operations/v1/vehicles/?status=active
GET /api/operations/v1/vehicles/?status=inactive
```

Returns existing `VehicleAsset` data:

- assignment
- plate number
- asset ID
- engine status
- telemetry location
- speed
- total distance
- distance today
- completed-order KM today
- computed KM variance

### KM Visibility

```http
GET /api/operations/v1/km-visibility/
GET /api/operations/v1/km-integrity/
GET /api/operations/v1/km-integrity/?status=failed
GET /api/operations/v1/km-integrity/?status=passed
GET /api/operations/v1/km-integrity/?status=unavailable
```

This uses existing `VehicleAsset` fields:

- `distance_today`
- `deliveries_km_today`

Status values:

- `passed`: both values are available and variance is within 10%.
- `failed`: both values are available and variance is above 10%.
- `unavailable`: there is not enough KM data to compare.

No new GPS records are created by these endpoints.

### Admin Console

Admin console endpoints are write-enabled and must only be shown to users where:

```json
{
  "role": "coo",
  "is_global": true
}
```

or users with a dispatcher admin profile.

Base path:

```text
/api/operations/v1/admin/
```

Create or update zones:

```http
GET  /api/operations/v1/admin/zones/
POST /api/operations/v1/admin/zones/
GET  /api/operations/v1/admin/zones/{zone_id}/
PUT  /api/operations/v1/admin/zones/{zone_id}/
PATCH /api/operations/v1/admin/zones/{zone_id}/
```

Zone payload fields:

```json
{
  "name": "Ajah",
  "description": "Ajah and nearby areas",
  "vertical": "vertical-uuid",
  "zone_lead": "vertical-lead-uuid-or-null",
  "center_lat": 6.4698,
  "center_lng": 3.5852,
  "radius_km": 5,
  "is_active": true
}
```

Create or update hubs:

```http
GET  /api/operations/v1/admin/hubs/
POST /api/operations/v1/admin/hubs/
GET  /api/operations/v1/admin/hubs/{hub_id}/
PUT  /api/operations/v1/admin/hubs/{hub_id}/
PATCH /api/operations/v1/admin/hubs/{hub_id}/
```

Hub payload fields:

```json
{
  "name": "NG-AJAH-STATION",
  "address": "Ajah, Lagos",
  "latitude": 6.4698,
  "longitude": 3.5852,
  "zone": "zone-uuid",
  "catchment_radius_km": 0.5,
  "hub_captain_name": "Captain Name",
  "hub_captain_phone": "080...",
  "is_active": true
}
```

Assign a hub to a zone by patching the hub `zone` field:

```http
PATCH /api/operations/v1/admin/hubs/{hub_id}/
```

```json
{
  "zone": "zone-uuid"
}
```

Set zone targets:

```http
GET  /api/operations/v1/admin/zone-targets/
POST /api/operations/v1/admin/zone-targets/
GET  /api/operations/v1/admin/zone-targets/{target_id}/
PUT  /api/operations/v1/admin/zone-targets/{target_id}/
PATCH /api/operations/v1/admin/zone-targets/{target_id}/
```

Target payload:

```json
{
  "zone": "zone-uuid",
  "month": "2026-05-01",
  "target_orders": 2000,
  "target_revenue": "600000.00"
}
```

The backend normalizes `month` to the first day of the month.

Assign vertical leads:

```http
GET  /api/operations/v1/admin/vertical-leads/
POST /api/operations/v1/admin/vertical-leads/
PATCH /api/operations/v1/admin/vertical-leads/{assignment_id}/
```

Payload:

```json
{
  "user": "user-uuid",
  "vertical": "vertical-uuid",
  "is_active": true
}
```

Assign zone captains:

```http
GET  /api/operations/v1/admin/zone-captains/
POST /api/operations/v1/admin/zone-captains/
PATCH /api/operations/v1/admin/zone-captains/{assignment_id}/
```

Payload:

```json
{
  "user": "user-uuid",
  "zone": "zone-uuid",
  "is_active": true
}
```

Assign riders to hubs:

```http
PATCH /api/operations/v1/admin/riders/{rider_id}/hub/
```

Payload:

```json
{
  "hub": "hub-uuid"
}
```

To remove a rider from a hub:

```json
{
  "hub": null
}
```

## Dashboard Screen Mapping

Main dashboard:

- `GET /me/`
- `GET /dashboard/summary/?period=<period>`
- `GET /flags/?limit=50`
- `GET /leaderboards/?period=<period>`
- `GET /verticals/?period=<period>`
- `GET /zones/?period=<period>`

Vertical detail:

- `GET /verticals/{id}/?period=<period>`
- `GET /verticals/{id}/zones/?period=<period>`

Zone detail:

- `GET /zones/{id}/?period=<period>`
- `GET /zones/{id}/riders/?period=<period>`
- `GET /merchants/?zone_id=<id>&period=<period>`
- `GET /jumia-hubs/?zone_id=<id>&period=<period>`

Rider detail:

- `GET /riders/{id}/?period=<period>`
- `GET /riders/{id}/performance/?period=<period>`
- `GET /riders/{id}/daily-activity/?period=<period>`
- `GET /riders/{id}/vehicle/`

Orders page:

- `GET /orders/?period=<period>`
- `GET /orders/analytics/?period=<period>`

Vehicle/KM page:

- `GET /vehicles/`
- `GET /km-visibility/`
- `GET /km-integrity/`

Admin console:

- `GET/POST /admin/zones/`
- `GET/PATCH /admin/zones/{id}/`
- `GET/POST /admin/hubs/`
- `GET/PATCH /admin/hubs/{id}/`
- `GET/POST /admin/zone-targets/`
- `GET/PATCH /admin/zone-targets/{id}/`
- `GET/POST /admin/vertical-leads/`
- `PATCH /admin/vertical-leads/{id}/`
- `GET/POST /admin/zone-captains/`
- `PATCH /admin/zone-captains/{id}/`
- `PATCH /admin/riders/{id}/hub/`

## Frontend Handling Notes

Use empty states when `results` is empty.

Do not display lease or hire-purchase values unless a future endpoint explicitly provides them.

For KM integrity:

- Show `unavailable` as a neutral state.
- Show `failed` as critical.
- Show `passed` as healthy.

For role scope:

- Hide global filters when `/me/` returns `is_global=false`.
- A vertical lead may only receive one vertical.
- A zone captain may only receive one zone.

For periods:

- Keep the selected period in route/query state.
- Pass the same `period` value to all dashboard endpoints that support it.
- For month dropdowns, send `YYYY-MM`, not month names.

## Phase 4 Hardening Checklist

Backend hardening should add tests for:

- `period=today`
- `period=yesterday`
- `period=this_week`
- `period=past_7_days`
- `period=this_month`
- `period=last_month`
- `period=this_year`
- `period=YYYY-MM`
- COO/admin scope
- vertical lead scope
- zone captain scope
- empty data responses
- order filters
- merchant filters
- KM integrity `passed`
- KM integrity `failed`
- KM integrity `unavailable`

Backend work completed for the screenshot period selector:

- `period=this_year` is supported by the parser.
- Tests have been added for `this_year` and `YYYY-MM`.
