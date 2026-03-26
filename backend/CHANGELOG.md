# Changelog

All notable changes to the AXpress backend are documented in this file.

---

## [2026-03-26] — Dispatcher Assignment Visibility Fix

### Fixed
- UI bug where dispatcher-assigned orders were incorrectly labeled as "RIDER CLAIMED".
- Missing `dispatcher_assigned` field in frontend `normalizeOrder` function.
- Local state update in `assignRider` and `changeStatus` now correctly reflects dispatcher assignment status.

---

## [2026-03-26] — Merchant Referral Registration

### Added
- Optional `referral_code` field to merchant signup endpoint.
- `referral_code` field to `User` and `Merchant` models.
- Database index on `LibertyPayUser.referral_code` for faster lookups.
- Logic to automatically link merchants to `LibertyPayUser` referrals during registration.

---

## [2026-03-26] — LibertyPay User Synchronization

### Added
- `LibertyPayUser` model in `referrals` app to store synced user data from external API.
- `sync_libertypay_users_task` Celery task to fetch and update user data from LibertyPay API.
- `sync_libertypay_users` management command to manually trigger the synchronization.
- `LIBERTYPAY_API_KEY` setting for authenticating with the LibertyPay API.

---

## [2026-03-24] — Hierarchy Restructuring: Rider Assignment via Hub

### Breaking Changes
- **Rider assignment now uses `hub` (RelayNode) instead of `zone` (home_zone).**
  - `PATCH /api/dispatch/riders/{id}/` now accepts `hub` (relay node UUID) instead of `zone`.
  - The `zone` field on rider responses is now **read-only**, derived from `hub.zone`.
  - The `hub` field is returned in rider responses as a new writable field.
  - Rider onboarding serializer accepts `hub` instead of `home_zone`.

### Added
- `hub` foreign key on `Rider` model pointing to `RelayNode` (commit `9c49733` by @Ayobami6).
- `role` field on `DispatcherProfile` with choices: `zone_lead`, `hub_captain`, `admin` (commit `9c49733` by @Ayobami6).
- `diagnose_hierarchy` management command to debug broken vertical/zone/rider FK links.
- ServiceAPIKey authentication on `RiderViewSet`, `RelayNodeViewSet`, and `MerchantViewSet` — OCC service keys can now access these dispatch endpoints.

### Changed
- **OCC analytics views** (`occ_views.py`): All rider lookups switched from `home_zone` to `hub__zone`.
  - `OCCVerticalListView` — rider aggregation via `hub__zone_id__in`
  - `OCCVerticalDetailView` — zone riders via `hub__zone`
  - `OCCZoneDashboardView` — rider count/active riders via `hub__zone`
  - `OCCZoneRidersView` — rider list via `hub__zone_id`
  - `OCCZoneLeaderboardView` — zone rider lookup via `hub__zone`
  - `OCCVerticalLeaderboardView` — vertical rider lookup via `hub__zone_id__in`
  - `OCCRiderLocationsView` — zone name via `hub.zone.name`
  - `OCCOrderAnalyticsView` — by-zone breakdown via `rider__hub__zone`
  - `_build_rider_data()` — target calculation via `hub.zone`
- **RiderSerializer** (`serializers.py`): `zone` field changed from writable `PrimaryKeyRelatedField(source="home_zone")` to read-only `SerializerMethodField` returning `hub.zone_id`. New `hub` field added as writable `PrimaryKeyRelatedField`.
- **RiderViewSet** (`views.py`): `select_related` updated from `home_zone` to `hub`, `hub__zone`.
- **Rider admin** (`admin.py`): `list_display`, `list_filter`, `autocomplete_fields`, and bulk assign action updated from `home_zone` to `hub`.
- **`notify_relay_vertical_leads`** (`tasks.py`): select_related chain and zone lookup updated to traverse `rider.hub.zone.vertical`.
- **`rebuild_leaderboard`** (`riders/management/commands/`): zone name derived from `rider.hub.zone`.

### Deprecated
- `Rider.home_zone` field — still in the database but no longer used by any view, serializer, or admin. Will be removed in a future migration.

---

## [2026-03-23] — OCC Service Key Auth for Dispatch Endpoints

### Added
- Explicit `ServiceAPIKeyAuthentication` on `RiderViewSet`, `MerchantViewSet`, and `RelayNodeViewSet` so the OCC service key (`sk_...`) can authenticate against `/api/dispatch/riders/`, `/api/dispatch/merchants/`, and `/api/dispatch/relay-nodes/`.

### Note
- `ZoneViewSet` and `VerticalViewSet` already had this; the other three were relying on the global default which was less explicit.
