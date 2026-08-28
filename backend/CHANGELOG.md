# Changelog

All notable changes to the AXpress backend are documented in this file.

---

## [2026-08-27] — Standardized Testing Framework & Tests Folder Organization (Unit & Integration)

### Added
- **Standardized Tests Directory Layout (`<app>/tests/unit/` & `<app>/tests/integration/`)**:
  - Restructured all tests across apps (`orders`, `riders`, `dispatcher`, `wallet`, `oprtn_dashboard`, `operations`, `subscriptions`, `authentication`, etc.) into dedicated `tests/unit/` and `tests/integration/` suites.
  - Added `__init__.py` package files across all test directories.
  - Cleaned up root loose test scripts, moving them to `scratch/`.
- **Standardized Test Runner Script (`run_tests.sh`)**:
  - Script for automated test execution that auto-detects active virtual environments (`venv` or `.venv`) and runs `pytest` with coverage reporting (`--cov=. --cov-report=xml --cov-report=term-missing`).
- **Coverage Configuration (`.coveragerc`)**:
  - Configured test coverage rules, omitting migrations, tests, management commands, factories, wsgi/asgi entry points, scripts, and utilities.
- **Pytest Configuration Alignment (`pytest.ini`)**:
  - Enhanced pytest discovery for all apps (`authentication`, `ax_merchant_api`, `bot`, `chats`, `crons`, `devs`, `dispatcher`, `operations`, `oprtn_dashboard`, `orders`, `referrals`, `riders`, `subscriptions`, `wallet`, `webhooks`, `whatsapp_messaging`), updated class/function patterns, ignored dirs, warning filters, markers, and coverage defaults.
- **Global Test Fixtures (`conftest.py`)**:
  - Added `override_static_storage` fixture (autouse) preventing missing static file/manifest errors during testing.
  - Added `authenticated_client` fixture alongside `auth_client` with type hinting and Google-style docstrings.
- **Makefile Test Automation**:
  - Updated `Makefile` with complete test suite targets (`make test`, `make test-fast`, `make test-cov`, `make test-unit`, `make test-integration`, `make test-api`, `make test-isolate`, `make migrations`, `make migrate`).

---

## [2026-08-26] — Google Places Autocomplete Session Usage Tracking

### Added
- **Google Autocomplete Session Usage Tracking**:
  - Model `GoogleAutoCompleteSessionUsage` (`orders/models.py`) to record session usage, pricing at $0.005 per session, query hits count, place resolution, and status lifecycle (`IN_PROGRESS`, `RESOLVED`, `EXPIRED`).
  - Recorded session token hits in `google_place_autocomplete` and session resolution in `google_place_details` (`orders/utils.py`).
  - Registered `GoogleAutoCompleteSessionUsageAdmin` in Django Admin (`orders/admin.py`) with filters, search, and raw ID fields.
  - Added migration `orders/migrations/0015_googleautocompletesessionusage.py`.
  - Added unit, integration, and E2E tests in `orders/test_google_autocomplete_session_usage.py`.

---

## [2026-08-06] — Fix Webhook Model ArrayField Base Field

### Fixed
- **Webhook Model ArrayField**: Added required positional argument `base_field=models.CharField(max_length=100)` and `blank=True` to `events` `ArrayField` in `webhooks/models.py`.

---

## [2026-07-23] — Dispatcher New Order Email Notification & MailNow Fallback

### Added
- **New Order Dispatcher Email Template**: Added `templates/emails/marketing/new_order_dispatcher.html` to render detailed information of newly created orders (including pricing, customer info, pickup and dropoff addresses).
- **Dispatcher Email Celery Task**: Added `send_new_order_dispatcher_email_task` in `orders/tasks.py` to send email alerts via Mailgun to all active dispatcher users when an order is created.
- **Dispatcher Email Signal**: Registered `notify_dispatchers_on_new_order` post_save signal in `orders/signals.py` to trigger the dispatcher notification email task upon order creation.
- **MailNow Fallback Email Utility**: Implemented `send_email_with_fallback` in `authentication/emails.py` that sends emails via Mailgun first, falling back to MailNow API (`POST https://api.mailnow.xyz/v1/email/send`) if Mailgun fails.
- **Unit Tests**: Added unit and integration tests in `orders/test_dispatcher_notification.py` to verify both the dispatcher order notifications and the MailNow email fallback resilience.

### Fixed
- **Order Charge Task Serialization**: Fixed a Celery task serialization error in `create_order_charge` task by returning a JSON-serializable string representation of the created Charge UUID instead of the Django model instance.
- **Task Unit Tests**: Added unit tests in `orders/tests.py` to verify that `create_order_charge` task runs successfully, returns a valid UUID string, creates the Charge database entry, and raises `Order.DoesNotExist` on invalid orders.

---

## [2026-07-13] — Mapbox Autocomplete Integration

### Added
- **Mapbox Geocoding v6 API integration**: Switched from Mapbox Search Box Suggest to the Geocoding v6 API forward search (`/search/geocode/v6/forward`) with `autocomplete=true` to fetch suggestions and geographic coordinates (`lat`/`lng`) in a single request.
- **Mapbox Autocomplete Support**: Integrated Mapbox autocomplete into `PlacesAutocompleteView` with support for session tokens.
- **Mapbox Place Details Support**: Updated `PlaceDetailsView` to retrieve feature details from Mapbox using prefix `mapbox:` and session tokens.
- **Fallback Chain**: Configured autocomplete to use Geoapify first, falling back to Mapbox, and finally falling back to AWS Location Service.
- **Autocomplete Coordinates Mapping**: Added support to map and return latitude and longitude coordinates directly in Geoapify and Mapbox autocomplete suggestions if present in the API response.
- **Unit Tests**: Updated integration tests in `orders/test_places.py` to cover Mapbox Geocoding v6 helpers, autocomplete, details, and fallback behaviors.

---

## [2026-07-09] — Google Places Fallback with AWS Location Service

### Added
- **AWS Location Service helpers**: Added AWS Location Service helper functions in `orders/utils.py` (`get_aws_location_client`, `aws_place_autocomplete`, `aws_place_details`, `aws_reverse_geocode`).
- **AWS Place Autocomplete, Details, Reverse Geocode, and Geocode Views**: Added REST API proxy views `PlacesAutocompleteView`, `PlaceDetailsView`, `ReverseGeocodeView`, and `GeocodeView` in `orders/places_views.py` wrapping AWS Location Service.
- **Endpoints routing**: Registered the new proxy endpoints in `orders/urls.py`.
- **AWS Places integration tests**: Added `orders/test_places.py` to cover helpers, proxy views, and geocoding fallbacks.

### Fixed
- **Geocoding graceful degradation fallback**: Modified `geocode_address` in `orders/utils.py` to fall back to AWS Location Service geocoding if Google Maps Geocoding API fails or throws an exception.

---

## [2026-07-03] — Fix Wallet process_pending_charges Idempotency

### Fixed
- **Wallet process_pending_charges Idempotency**: Fixed a bug in `Wallet.process_pending_charges` where orders/sub-orders payment status was skipped and left as `Pending` when a matching transaction had already been debited successfully but the status update was interrupted.
- **Unit Tests**: Added `ProcessPendingChargesIdempotencyTest` in `wallet/tests.py` to verify that order and sub-orders payment status are correctly synced when a transaction already exists.

---

## [2026-06-24] — Export Rider Distance Covered command

### Added
- **Rider Distance Export Command**: Added `export_rider_distances` management command under `dispatcher` app. It calculates rider distance covered for a specified date range based on `VehicleTracking` odometer logs and outputs a styled Excel sheet with zebra-striping, custom alignments, and auto-fitted column widths.
- **Unit Tests**: Added `ExportRiderDistancesCommandTests` in `dispatcher/tests.py` to assert correct distance calculations, Excel headers, formatting, and file generation.

---

## [2026-06-08] — Amortization Transaction Import/Export Support

### Added
- **Amortization Transaction Import/Export**: Integrated `django-import-export` into `AmortizationTransactionAdmin` in `wallet/admin.py`, defining `AmortizationTransactionResource` to support CSV/Excel import and export of bike hire-purchase transactions. Includes customized fields for User Name and User Phone.

---

## [2026-06-04] — Fix Admin Charge Change Page Timeout

### Added
- **Makefile Update**: Added a `test` target to run the pytest test suite via `.venv/bin/pytest` or system fallback.

### Fixed
- **Order representation N+1 query optimization**: Optimized the `Order` model's `__str__` method to return only the order number (`f"Order {self.order_number}"`), avoiding heavy database query loops on related user objects when rendering list choices.
- **Admin models raw_id_fields optimization**: Added `raw_id_fields` to foreign key relationships in all `wallet` and `orders` admin modules (`ChargeAdmin`, `WalletAdmin`, `TransactionAdmin`, `VirtualAccountAdmin`, `WebhookLogAdmin`, `AmortizationWalletAdmin`, `AmortizationTransactionAdmin`, `AmortizationVirtualAccountAdmin`, `OrderAdmin`, `DeliveryAdmin`, `OrderLegAdmin`, `MerchantPricingOverrideAdmin`, `MerchantPriceListAdmin`, `MerchantPriceListItemAdmin`). This completely prevents Django admin from executing N+1 select list queries or rendering massive dropdown lists, fixing the gunicorn timeout crash when displaying admin change pages.

---

## [2026-05-19] — Route-Based Proximity & Wallet Test Fixes

### Added
- **Rider Earning Signal Handler**: Implemented a Django model signal in `riders/signals.py` (`credit_rider_wallet_on_earning`) that listens to the `post_save` event on `RiderEarning`. It automatically and atomically credits the rider's wallet with the correct `net_earning` amount, generating a clean `EARN-` transaction reference and description.

### Changed
- **Transaction Pagination Layout**: Overrode the `get_paginated_response` method of `TransactionPagination` in `wallet/views.py`. This resolves layout conflicts between API users by conditionally pulling the `"success"` and `"data"` fields to the top-level format when requested, satisfying unit tests and backward compatibility.
- **Rider Proximity Check (Pickup & Completion)**: Replaced straight-line `Zone.haversine_distance` calculation with real route-based distance calculation using Google Maps/OSRM-based `calculate_route` helper in both the order status advance logic (`_advance_order` in `orders/views.py`) and the order completion logic (`OrderCompleteView` in `orders/views.py`). Included a defensive fallback to `haversine_distance` if the routing service is offline or unavailable.
- **Proximity Restriction Tests**: Overhauled `orders/test_proximity_restrictions.py` to correctly initialize rider coordinates, mock routing API responses via `unittest.mock.patch`, and verify both successful routing API results and graceful haversine fallbacks for both pickup and completion views.

### Fixed
- **Vehicle Asset Orders Today Count**: Corrected `orders_today` field on `VehicleAssetSerializer` in `dispatcher/serializers.py` to be a `SerializerMethodField` rather than mapping to telemetry/distance. Added `get_orders_today` helper to accurately sum completed orders today with robust local timezone-aware fallbacks for missing completion and delivery timestamps, resolving multiple failing test assertions.

---
## [2026-05-06] — Bike Amortization System (Phase 1)

### Added
- **Amortization Models**: Implemented core models for tracking bike hire-purchase payments.
    - `AmortizationWallet`: Dedicated locked wallet for riders to track their progress towards bike ownership.
    - `AmortizationTransaction`: Ledger for recording payments and balance changes within the amortization wallet.
    - `AmortizationVirtualAccount`: Support for assigned virtual bank accounts dedicated to amortization payments.
- **Admin Management**: Registered all amortization models in the Django Admin interface with custom list views, search, and filters.
- **Rider Admin Action**: Added "Create amortization wallet for selected riders" action to the Rider admin to allow bulk wallet initialization.
- **Wallet Admin Actions**: Added "Activate" and "Deactivate" actions to the Amortization Wallet admin for status management.



### Fixed
- **AmortizationWallet Typo**: Corrected a typo in the `ownership_percentage` property calculation.

---

## [2026-05-04] — Email Service Resilience & Fallback

### Added
- **MailNow Service Integration**: Implemented `MailNowService` in `dispatcher/utils.py` to provide a secondary email dispatch channel via a local MailNow API service (port 3200).
- **Email Fallback Mechanism**: Integrated automatic fallback logic into `MailgunEmailService`.
    - If a Mailgun dispatch fails (e.g., due to API errors, timeouts, or invalid credentials), the system automatically retries the request using `MailNowService`.
    - Supports both standard onboarding emails and CSV attachments with base64 encoding.
- **MailNow Configuration**: Added `MAILNOW_API_URL` and `MAILNOW_API_KEY` settings to support the new service.

---

## [2026-04-24] — Vehicle Tracking Tools

### Added
- **Vehicle History Command**: Created `get_vehicle_history` management command to retrieve historical telemetry for a specific rider (by riderID) within a date range.

---

## [2026-04-23] — Data Integrity, Reassignment Tracking & Record Protection

### Added
- **Vehicle Reassignment History**: Implemented comprehensive tracking of vehicle movements between riders.
    - Added `VehicleReassignment` model with `from_rider`, `to_rider`, and `admin` tracking.
    - Records are automatically created during every `assign_vehicle` action.
- **Rider Soft Delete**: Implemented a robust soft-delete mechanism for the `Rider` model.
    - Added `is_deleted` field and `SoftDeleteManager`/`SoftDeleteQuerySet`.
    - `Rider.objects.all()` now automatically excludes soft-deleted riders.
    - Overridden `Rider.delete()` to perform soft deletion instead of database removal.
- **Record Protection (Admin)**: Disabled Django Admin deletion for mission-critical models to prevent accidental data loss.
    - Affected models: `Rider`, `VehicleAsset`, `Transaction`, `Charge`.
    - Removed the "Delete" button from individual record views and the "Delete selected" bulk action from list views.

### Changed
- **Vehicle Assignment Restriction**: Restricted the `assign_vehicle` endpoint to users with the `admin` dispatcher role.

---
 
 ## [2026-04-22] — Partner Orders & Order Creation Refactor
 
 ### Added
 - **Partner Order Support**: Added ability for dispatchers to create orders for partners.
     - New fields in `OrderCreateSerializer`: `is_partner_order`, `partner_order_count`, `file_uploaded_url`.
     - These fields are persisted to the `Order` model when `is_partner_order` is True.
- **Partner Order Constraints**:
    - Validates that the merchant is a partner before processing.
    - Automatically calculates `total_amount` as `partner_base_price * partner_order_count`.
    - Allows skipping of pickup/delivery details, providing sensible defaults when omitted.
 
 ### Changed
 - **Refactored Order Creation**: Moved core order creation logic from `OrderCreateSerializer` to `IOrderService.create_dispatcher_order` to reduce complexity and improve maintainability.
 - **Service Layer Enhancements**:
     - Added `create_dispatcher_order` to `OrderService` interface and implementation.
     - Added `process_partners_order` to handle partner-specific logic within the service layer.
 
 ---
 

## [2026-04-21] — Merchant Notification Management

### Added
- **Delete Merchant Notification**: Implemented endpoints for merchants to delete notifications.
    - `DELETE /api/auth/notifications/<uuid:pk>/`: Delete a single notification.
    - `DELETE /api/auth/notifications/delete-all/`: Clear all notifications for the merchant.
- **Improved Logging**: Integrated `@exception_advice` with `ErrorLog` for consistent error tracking in notification views.

---

## [2026-04-20] — Parcel Service Refactor & Bug Fixes

### Changed
- **Refactored `OrderService`** in `orders/services.py`:
    - Renamed `process_percel_delivery` to `process_parcel_delivery` (fixed typo).
    - Fixed a critical **`NameError`** where `list_response` was used before definition when `is_pickup` was False.
    - Improved logic to safely separate pickup and delivery workflows.
    - **Removed unsafe side-effects**: The service no longer mutates the `request_data` dictionary. Instead, it returns updated `pickup_address` and `dropoff_address` in the response dictionary.
- **Updated `QuickSendView`** in `orders/views.py`:
    - Updated call to the renamed `process_parcel_delivery` method.
    - **Fixed logic bug**: `is_percel_order` flag is now correctly calculated as `is_pickup_percel or isdelivery_percel` instead of being hardcoded to `False`.
    - Explicitly update validated data with addresses returned from the service.

---

## [2026-04-20] — Performance Optimization: Notification Backgrounding

### Changed
- **Optimized Rider Notifications** in `orders/views.py`:
    - Moved real-time push notifications into background threads to reduce API latency and prevent external service delays from blocking the request-response cycle.
    - Affected views: `OrderStartView`, `OrderStatusChangeView` (for the "start" action), and `OrderCompleteView`.

---

## [2026-04-09] — AI Agent Context & UUID Validation
- **AI Agent Fix**: Resolved an issue where the AI Support Agent would hallucinate a placeholder `user_1234` ID when calling tools.
    - **Injected Context**: Explicitly prepending `[SYSTEM CONTEXT: User ID = ...]` to user messages in `get_ai_response`.
    - **Robust Validation**: Added `uuid.UUID` validation in `get_user_profile` to prevent `ValidationError` crashes, returning helpful errors to the agent instead.
    - **Instruction Update**: Refined the `SupportCoordinator` instruction to explicitly look for the provided User ID in the context.
- **Cleanup**: Removed redundant debug print statements in Celery tasks.

---

## [2026-04-17] — Rider Trips Period Filtering

### Changed
- **Updated `RiderTodayTripsView`** in `riders/views.py`: Added support for period filtering (`today`, `week`, `month`) via the `period` query parameter, matching the logic in the Earnings view.
- **Updated `ENDPOINTS_DOCUMENTATION.md`**: Documented the period filtering for Today's Trips.

---

## [2026-04-15] — SmartParcel V2 Business API Overhaul

### Changed
- **Overhauled SmartPercelIntegration class** in `orders/services.py`: Corrected the integration to match the SmartParcel V2 Business requirements.
    - All external requests now use the **POST method**.
    - Authentication **apikey** is now sent within the JSON request body instead of headers.
    - Updated endpoint paths: `/states/`, `/cities/state/`, `/boxes/city/`, `/boxes/info/`, `/sizes/`, `/parcels/create/`, `/parcels/info/all/`, `/parcels/cancel/`.
    - Added `list_assigned_boxes()` — retrieve the list of boxes assigned to the merchant.
- **Refactored `orders/views.py`**:
    - Updated `SmartParcelCreateParcelView` to map internal snake_case fields to the external API's required field names (e.g., `recipientname`, `boxid`, `sizeid`).
    - Consolidated several retrieval views and removed defunct endpoints (e.g., `SmartParcelCitiesView` and `SmartParcelBoxesView` which are not supported in the Business V2 spec).
    - Updated `SmartParcelAvailableBoxesView` to require a `city_id` query parameter.
    - Added `SmartParcelAssignedBoxesByCityView` to fetch assigned boxes for a specific city.
- **Updated `orders/urls.py`**: Added `SmartParcelAssignedBoxesByCityView` and removed defunct URL patterns.
- **Updated `ENDPOINTS_DOCUMENTATION.md`**: Simplified and corrected the documentation for the Locker Delivery Integration, including the new Assigned Boxes endpoint.

### Removed
- Defunct endpoints: `GET /cities/`, `GET /boxes/`, `GET /parcels/<tracking_number>/timeline/`.

---

## [2026-04-10] — Dashboard & Weekly Reports
- **Vertical Lead Visibility**: Added `vertical_lead_name` to the dispatcher dashboard order list.
    - Updated UI table with a new "Vertical Lead" column.
    - Included `vertical_lead_name` in the CSV export data.
    - Updated `OrderSerializer` to include the lead name derived from the order's vertical.
- **Weekly Delivery Report Enhance**: Added `total_order_amount` to the weekly Monday reports (E1 template).
    - Calculated total order amount for all orders requested during the past week.
    - Updated `tasks.py` to include the amount in the email context, formatted with commas.
    - Updated `E1.html` template to display the total order amount with a Naira symbol.
- **Rider Performance Metrics**: Added comprehensive order and distance metrics to the Django Admin.
    - Implemented real-time order counts for Today, This Week (starting Monday), and This Month.
    - Added "Overall Orders" and "Distance All Time" (km) tracking.
    - Integrated metrics into the Rider list view and CSV export functionality via `RiderResource`.
    - Added property methods to the `Rider` model for programmatic access to performance data.

---

## [2026-04-07] — Chats API & Merchant Deactivation
- **Ably Realtime Chats Documentation**: Created [ably_realtime_chats.md](file:///Users/mac/Liberty/aexpress/backend/ably_realtime_chats.md) guide for client-side integration.
- **`subscribe_chat` Management Command**: Added a new command to subscribe to real-time chat messages for debugging.
- **Chats API Documentation**: Documented the Chat System REST API in `ENDPOINTS_DOCUMENTATION.md`.
- **Merchant Deactivation (Delete)**: Implemented new endpoints for soft-deactivating merchant accounts.
    - **Dispatcher Portal**: Admins can deactivate merchants via `DELETE /api/dispatcher/merchants/<id>/`.
    - **Merchant Portal**: Merchants can deactivate their own accounts via `DELETE /api/auth/profile/`.
- **Validation**: Added a check to prevent deactivation if a merchant has any active/ongoing orders (Pending, Assigned, Started, etc.) in both endpoints.
- **REST API Documentation**: Created and updated `ENDPOINTS_DOCUMENTATION.md` to document the new capabilities.

---

## [2026-04-02] — Grouped Order Mode

### Added
- **Grouped Order Mode**: Introduced a new `grouped` mode for single-delivery orders within the "Quick Send" flow.
- **Backend Model**: Updated `Order.MODE_CHOICES` to include `grouped`.
- **API Support**: Updated `QuickSendSerializer` to accept a `mode` field (`quick` or `grouped`) and `QuickSendView` to persist it.
- **Frontend Toggle**: Added a "Quick Send" vs "Grouped Order" toggle in the `NewOrderScreen` component, allowing merchants to categorize their deliveries.

---

## [2026-03-31] — Merchant API Key Authentication Class

### Added
- **`MerchantAPIKeyAuthentication`** in `dispatcher/authentication.py`: A DRF `BaseAuthentication` subclass that validates `ak_live_` prefixed API keys.
    - Resolves to the real Django `User` object, so `request.user` works normally on any secured view.
    - Tracks `last_used_at` on each successful request.
    - Designed to be used alongside JWT auth via `authentication_classes`:
      ```python
      from dispatcher.authentication import MerchantAPIKeyAuthentication
      from rest_framework.settings import api_settings

      authentication_classes = [
          MerchantAPIKeyAuthentication,
          *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
      ]
      ```

---

- Registered `Webhook` and `WebhookOutbox` models in the Django Admin for the `webhooks` app, enabling internal management of webhook configurations and inspection of delivery attempts.

---

## [2026-03-30] — Merchant API Access Request

### Added
- **Merchant API Access Request**: New endpoint for regular merchants to switch their account type to `api`, enabling API key management.
- **API Endpoints**: 
    - `POST /api/merchant/request-api-access/`: Switches a merchant's account type to `api` (JWT authenticated).

### Changed
- **OTP Request Cleanup**: Optimized the `MerchantAPIKeyRequestOTPView` logic and removed redundant type checks.

---

## [2026-03-30] — Merchant API Key Authentication

### Added
- **Merchant API Key System**: Implemented a secure, two-step OTP-based retrieval and rotation flow for merchants of type `api`.
- **Models**: Added `MerchantAPIKey` model in `dispatcher` app to store hashed API keys (`ak_live_` prefix).
- **API Endpoints**: 
    - `POST /api/merchant/apikey/request-otp/`: Requests a 6-digit OTP for API key management (JWT authenticated).
    - `POST /api/merchant/apikey/retrieve/`: Verifies the OTP and returns a newly generated raw API key (JWT authenticated).
- **Security**: API keys are stored as SHA-256 hashes; raw keys are only displayed once during generation. Rotation is supported and overwrites the previous key.


 ## [2026-03-28] — Frontend Tiered Pricing Fix
 
 ### Fixed
 - **Tiered Pricing Calculation**: Fixed a bug in `NewOrderScreen.tsx` where the tiered pricing logic was hardcoded to stop after 3 tiers, causing incorrect (higher) rates to be applied to long-distance deliveries. Replaced with a generic loop matching the backend behavior.

### Added
- **Order Admin Enhancement**: Added "Rider Earning" column and detail field to the `Order` model in Django Admin, showing the net earning for the assigned rider (or 0.00 if not available).
- **Delivery Inline Enhancement**: Added `dropoff_latitude` and `dropoff_longitude` to the `Order` admin's `DeliveryInline` for better visibility of dropoff coordinates.

 
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
