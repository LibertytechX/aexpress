# Assured Express Operations Dashboard Implementation Plan

## Purpose

This document defines the fresh implementation plan for the Assured Express operations dashboard.

The existing `/api/occ/` endpoints should be treated as legacy/internal reference only. They should not be extended as the new product contract. The new dashboard API should be built under a clean namespace:

```text
/api/operations/v1/
```

The frontend will not live in this repo. Engineering should provide the frontend developer with a new API documentation package and implementation guide based on the endpoints defined here.

## Product Goal

Build a role-based operations dashboard that gives the COO, vertical leads, and zone captains a clear real-time view of:

- Rider activity
- Order performance
- Zone and vertical health
- GPS KM versus order KM integrity
- Available vehicle/KM status
- Merchant activity
- Jumia hub/rider deployment
- Operational flags that need attention

## Architectural Direction

The dashboard should be built in this repo because the required source data already lives here: riders, orders, merchants, vehicles, zones, hubs, telemetry, targets, and existing operational models.

The frontend should consume the new API as an external client. The backend should expose a stable product contract and keep implementation details inside the Django codebase.

Recommended backend structure:

- Keep existing `/api/occ/` endpoints untouched except for bug fixes required by current consumers.
- Build new endpoints under `/api/operations/v1/`.
- Put dashboard business logic in service/query modules, not directly inside views.
- Do not add new models or migrations for this dashboard work.
- If a business requirement has no existing model or reliable data source, omit it from the API or expose it as unavailable rather than inventing persistence.
- Use role-based scoping at the API layer so users only see their permitted verticals, zones, and riders.

## Role Scoping

The same API should support different dashboard scopes based on the authenticated user:

- COO / admin: all verticals, zones, riders, merchants, available vehicle/KM data, and computed flags.
- Vertical lead: assigned vertical, all zones and riders under that vertical.
- Zone captain: assigned zone, riders and merchants under that zone.

Phase 1 must confirm the exact user/profile model fields to use for these roles.

## Endpoint Summary

Target first full release: dashboard-only endpoint count based on existing data.

MVP read-only dashboard release: approximately 13 endpoints.

The endpoint count may change slightly during implementation if two resources are better merged or if a business workflow requires a separate write endpoint.

## Phase 0: Discovery And Retirement Plan

Goal: establish what already exists and define the clean boundary for the new dashboard.

Tasks:

- Review current models for riders, orders, merchants, vehicles, hubs, zones, verticals, dispatcher profiles, GPS tracking, and snapshots.
- Confirm which existing fields are reliable enough for the dashboard.
- Identify dashboard requirements that cannot be supported from existing models and mark them out of scope for now.
- Mark `/api/occ/` as legacy/internal in documentation.
- Decide whether the new code lives in a new Django app such as `operations` or inside `dispatcher` as an isolated module.

Deliverables:

- Data availability report.
- Unsupported data list.
- Legacy OCC retirement note.
- Confirmed API namespace: `/api/operations/v1/`.

## Phase 1: Existing Data Mapping

Goal: map the dashboard to data that already exists in the backend.

Existing models to reuse where possible:

- `Vertical`
- `Zone`
- `RelayNode`
- `Rider`
- `VehicleAsset`
- `Merchant`
- `RiderDailySnapshot`
- `MerchantDailySnapshot`
- `ZoneTarget`
- `VerticalLead`
- `ZoneCaptain`

Tasks:

- Map each dashboard card/table to current models and fields.
- Confirm how rider scope is derived from `Rider.hub -> RelayNode.zone -> Zone.vertical`.
- Confirm which vehicle/KM fields can be used from `VehicleAsset` and `VehicleTracking`.
- Confirm whether any hire-purchase or lease data already exists elsewhere in the repo.
- Mark unavailable requirements as out of scope instead of adding new tables.

Deliverables:

- Field mapping document.
- Unsupported data list.
- Dashboard API response contract using existing data only.

## Phase 2: Service Layer And Metrics

Goal: centralize dashboard calculations before building the external API contract.

Service modules should calculate:

- Dashboard summary metrics.
- Vertical rollups.
- Zone rollups.
- Rider performance.
- Order analytics.
- Merchant activity.
- Available vehicle/KM status.
- Computed operational flags from existing fields.
- Leaderboards.

Important implementation rules:

- Keep calculations testable outside API views.
- Avoid duplicating query logic across endpoints.
- Use snapshots for historical periods where available.
- Use live order/vehicle data for current-day metrics where freshness matters.
- Return safe defaults when optional data is missing.

Deliverables:

- Operations query/service modules.
- Unit tests for core calculations.
- Internal serializer/data contract definitions.

## Phase 3: MVP Read-Only Dashboard APIs

Goal: provide the frontend developer with enough APIs to build the first dashboard experience.

Endpoints:

1. `GET /api/operations/v1/me/`
   - Current user, role, assigned scope, permissions.

2. `GET /api/operations/v1/dashboard/summary/`
   - Top-level operational KPIs for the user's scope.

3. `GET /api/operations/v1/dashboard/flags/`
   - Current issues requiring attention.

4. `GET /api/operations/v1/verticals/`
   - Vertical list with performance rollups.

5. `GET /api/operations/v1/verticals/{id}/`
   - Vertical detail.

6. `GET /api/operations/v1/verticals/{id}/zones/`
   - Zones under one vertical.

7. `GET /api/operations/v1/zones/`
   - Zones visible to current user.

8. `GET /api/operations/v1/zones/{id}/`
   - Zone detail and health.

9. `GET /api/operations/v1/zones/{id}/riders/`
   - Riders in a zone with status and summary metrics.

10. `GET /api/operations/v1/riders/{id}/`
    - Rider profile and operational assignment.

11. `GET /api/operations/v1/riders/{id}/performance/`
    - Rider performance metrics for a selected period.

12. `GET /api/operations/v1/riders/{id}/daily-activity/`
    - Day-by-day rider activity.

13. `GET /api/operations/v1/leaderboards/`
    - Rider, zone, and vertical rankings.

Common filters:

- `period=today|yesterday|this_week|past_7_days|this_month|last_month|YYYY-MM`
- `vertical_id`
- `zone_id`
- `rider_id`
- `status`

Deliverables:

- MVP API endpoints.
- Authentication and role scoping.
- API tests for COO, vertical lead, and zone captain visibility.
- Draft frontend API documentation.

## Phase 4: Orders, Merchants, And Jumia Visibility

Goal: expose the supporting operational views needed to investigate dashboard numbers.

Endpoints:

14. `GET /api/operations/v1/orders/`
    - Operational order list with filters.

15. `GET /api/operations/v1/orders/analytics/`
    - Completion, failure, revenue, and distance trends.

16. `GET /api/operations/v1/merchants/`
    - Merchant visibility by zone, rider, activity status, and order behavior.

17. `GET /api/operations/v1/jumia-hubs/`
    - Jumia hub list, mapped zones, assigned riders, and deployment status.

Deliverables:

- Order analytics APIs.
- Merchant activity APIs.
- Jumia hub assignment visibility.
- Frontend guide update for drill-down workflows.

## Phase 5: Available Vehicle And KM Visibility

Goal: expose vehicle and KM visibility using only existing fields.

Endpoints:

18. `GET /api/operations/v1/vehicles/`
    - Vehicle assets, assignment status, current telemetry fields, and available KM fields.

19. `GET /api/operations/v1/riders/{id}/vehicle/`
    - Rider vehicle assignment and available vehicle telemetry.

20. `GET /api/operations/v1/km-visibility/`
    - Available GPS/vehicle KM versus order KM summary from existing `VehicleAsset` fields.

Unsupported for now:

- Lease agreement status.
- Lease payment history.
- Missed payment reconciliation.
- Hire-purchase amortisation.

These should not be implemented unless matching data already exists in the current system.

Deliverables:

- Vehicle list API.
- Rider vehicle API.
- KM visibility API from existing fields.

## Phase 6: Computed KM And Operations Flags

Goal: compute dashboard flags using only existing data.

Endpoints:

21. `GET /api/operations/v1/flags/`
    - Computed operational flags from available data.

22. `GET /api/operations/v1/km-integrity/`
    - Read-only computed KM variance from existing `VehicleAsset.distance_today` and `VehicleAsset.deliveries_km_today`.

Business rule:

For each rider and working day:

```text
variance = abs(order_km - gps_km) / max(gps_km, order_km)
```

If the variance is greater than 10%, return a critical computed flag in the API response.

Important implementation notes:

- Do not store new GPS KM records.
- Do not create persisted KM integrity checks.
- Do not trigger automatic enforcement actions.
- The dashboard should show pending, passed, warning, and failed integrity states.

Deliverables:

- Read-only KM integrity API.
- Computed flag API.
- Tests for pass/fail threshold behavior using existing fields.

## Phase 7: Documentation Package For Frontend

Goal: provide the frontend developer with everything needed to build against the new backend contract.

Deliverables:

- API overview.
- Authentication guide.
- Role and permission behavior.
- Endpoint list.
- Query filter guide.
- Response examples.
- Error response format.
- Dashboard screen-to-endpoint mapping.
- Postman collection or OpenAPI schema.
- Implementation notes for loading, empty, and error states.

## Phase 8: Verification And Launch Readiness

Goal: confirm the dashboard can support real operations usage.

Checklist:

- COO can view all verticals, zones, riders, orders, leases, and flags.
- Vertical lead can only view assigned vertical data.
- Zone captain can only view assigned zone data.
- Dashboard summary returns safe defaults when optional data is missing.
- Rider performance matches underlying order data.
- KM integrity API returns violations above 10% when existing KM fields are available.
- Unsupported lease/payment data is not exposed as if it exists.
- API documentation matches actual responses.
- Legacy `/api/occ/` endpoints are not referenced by new frontend documentation.

## Recommended Build Order

1. Phase 0: discovery and retirement plan.
2. Phase 1: existing data mapping.
3. Phase 2: service layer and metrics.
4. Phase 3: MVP read-only dashboard APIs.
5. Phase 7: first frontend documentation package.
6. Phase 4: orders, merchants, and Jumia visibility.
7. Phase 5: available vehicle and KM visibility.
8. Phase 6: computed KM and operations flags.
9. Phase 8: verification and launch readiness.

## Initial Endpoint Count

The planned dashboard-only release contains 22 endpoints:

- 13 MVP dashboard read endpoints.
- 4 orders, merchants, and Jumia endpoints.
- 3 vehicle and KM visibility endpoints.
- 2 computed flag and KM integrity endpoints.

The first implementation milestone should target the 13 MVP read endpoints, then expand only into dashboard views that can be backed by existing system data.
