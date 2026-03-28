# Changelog

All notable changes to the AXpress backend are documented in this file.

---
 
 ## [2026-03-28] — Frontend Tiered Pricing Fix
 
 ### Fixed
 - **Tiered Pricing Calculation**: Fixed a bug in `NewOrderScreen.tsx` where the tiered pricing logic was hardcoded to stop after 3 tiers, causing incorrect (higher) rates to be applied to long-distance deliveries. Replaced with a generic loop matching the backend behavior.
 
 ---

## [2026-03-27] — Postpaid Payment Plan Feature

### Added
- **Postpaid Billing System**: Launched a new postpaid payment method for merchants with weekly and monthly options.
- **Models**: Added `PostpaidPlan`, `MerchantPostpaidSubscription`, and `PostpaidInvoice` to the `subscriptions` app.
- **Order Integration**: Added `postpaid` payment method to `Order` model and integrated accumulation logic in `QuickSend`, `MultiDrop`, and `BulkImport` views.
- **Automated Billing**: Implemented `process_postpaid_billing_cycles` Celery task for automated period rotation and invoice generation.
- **Payment Blocking**: Automated blocking of order creation for merchants with unpaid postpaid invoices.
- **API Endpoints**: New suite of endpoints for listing/activating postpaid plans and managing invoices.

---

## [2026-03-27] — Subscription Payment Model & Deferred Overage Billing

### Added
- New `subscriptions` app for merchant plans and automated invoicing.
- Models: `SubscriptionPlan`, `MerchantSubscription`, `SubscriptionUsage`, `SubscriptionOverage`, `SubscriptionInvoice`, `MerchantDedicatedRider`.
- Celery tasks `process_subscription_invoicing` and `process_invoice_payment` for hands-free billing cycles.
- Integrated subscription checks into `QuickSend`, `MultiDrop`, and `BulkImport` views for zero-upfront order creation.
- Dedicated rider prioritization in `process_order_proximity` dispatch logic.
- **Dynamic Virtual Accounts**: Implemented 30-minute one-time virtual accounts for subscription invoices with automated webhook reconciliation (`SUB-INV-` prefix).
- **Invoice Management API**: New endpoints for listing subscriptions and refreshing invoice virtual accounts.

- **Order Completion Offloading**: Moved heavy post-order completion logic (streaks, challenges, and commissions) from the synchronous signal handler to a background Celery task (`handle_order_completion_tasks`) to reduce endpoint latency.

### Fixed
- `TypeError` in `Zone.haversine_distance` caused by mixed `float` and `Decimal` coordinate types during distance calculations (e.g., during order pickup/completion).

---

## [2026-03-26] — Transaction Admin Balance Tracking & Charge Soft Delete

### Added
- `is_active` field to `Charge` model to support soft deletion.
- `soft_delete_charges` action to `ChargeAdmin` for deactivating charges.

### Changed
- Added `balance_before` and `balance_after` to the `list_display` of `TransactionAdmin` for better visibility of wallet balance changes.
- Updated `ChargeAdmin` to display `is_active` and include it in filters.

---

2: 
3: ## [2026-03-26] — Order Status Fix Management Command
4: 
5: ### Added
6: - `fix_assignment_accepted_status` management command to update orders from "AssignmentAccepted" to "Assigned".
7: - Automatic `OrderEvent` logging for order status fixes.
8: 
9: ---
10: 11: 3: ## [2026-03-26] — Buddy Referral Commission (LibertyPay)
4: 
5: ### Added
6: - `send_buddy_referral_commission_task` Celery task to send commissions to LibertyPay users via external API.
7: - `LIBERTYPAY_TRANSACTION_PIN` setting for authorizing buddy commission transfers.
8: - Integration with `on_order_completed` signal to automatically trigger buddy commissions when a merchant with a referral code completes an order.
9: 
10: ---

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
