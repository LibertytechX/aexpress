All notable changes to the AXpress project are documented in this file.

# [2026-07-30] — Add OrderEvent to Django Admin

### Backend
#### Added
- **OrderEvent Admin Registration**: Registered the `OrderEvent` model in Django admin (`orders/admin.py`) as a standalone model with raw_id_fields, search, and list filters.
- **OrderEvent Admin Inline**: Added `OrderEventInline` inside `OrderAdmin` to display all event logs directly within the parent Order view in Django admin.
- **Admin Unit Tests**: Added verification tests in `orders/tests.py` to ensure `OrderEventAdmin` has optimized `raw_id_fields` for performance.

#### Fixed
- **Status Template Map Mappings**: Fixed missing `AssignmentAccepted` and `AssignmentRejected` status entries in `status_template_map` inside `orders/signals.py`, fixing test failures in `test_merchant_emails.py`.

---

# [2026-07-30] — Merchant Email Notifications on Order Progression Stages

### Backend
#### Added
- **Order Progression Email Templates**: Designed and added 10 premium, brand-aligned email templates under `backend/templates/emails/marketing/` (extending `base.html` with Outfit typography) for order lifecycle states: Pending, Assigned, Assignment Accepted, Assignment Rejected, Picked Up, Fulfilling, Arrived, Customer Canceled, Rider Canceled, and Failed.
- **Order Status Signal Receiver**: Registered `send_merchant_email_on_status_change` receiver for the `post_save` signal on the `Order` model in `orders/signals.py`. It tracks status transitions from the previous value (populated by `pre_save`) and triggers the corresponding transactional email.
- **Email Signal Unit Tests**: Created `orders/test_merchant_emails.py` containing the `MerchantProgressionEmailsTest` class to verify transactional email triggers, idempotency check bypasses, and transition boundaries.

#### Improved
- **Celery Transactional Task Route**: Updated the `_send_marketing_email` helper and `send_transactional_email` task in `orders/tasks.py` to support a `skip_daily_check` flag. This allows transactional order progression emails to bypass the daily campaign rate-limiting check while preserving per-order-and-stage idempotency.
- **Controller Cleanup**: Removed redundant manual Celery task dispatches from `_advance_order` and `DeliveryCompleteView` in `orders/views.py`, delegating all progression emails to Django model signals.

---

# [2026-07-23] — Dispatcher Notifications & Order Charge Task Serialization Fix

### Backend
#### Added
- **New Order Dispatcher Email Template**: Added HTML template to render detailed information of newly created orders for dispatcher alerts.
- **Dispatcher Email Celery Task & Signal**: Added task `send_new_order_dispatcher_email_task` and registered post_save signal `notify_dispatchers_on_new_order` to trigger notifications on order creation.
- **MailNow Fallback Email Utility**: Implemented `send_email_with_fallback` in `authentication/emails.py` falling back to MailNow API if Mailgun fails.

#### Fixed
- **Order Charge Task Serialization**: Fixed a Celery task serialization error in `create_order_charge` task by returning a JSON-serializable string representation of the created Charge UUID instead of the Django model instance.
- **Task Unit Tests**: Added unit tests in `orders/tests.py` to verify that `create_order_charge` task runs successfully, returns a valid UUID string, creates the Charge database entry, and raises `Order.DoesNotExist` on invalid orders.

---

# [2026-07-14] — SmartParcel API Error Handling

### Backend
#### Fixed
- **SmartParcel API Error Parsing**: Updated `SmartPercelIntegration.create_parcel` in [services.py](file:///Users/mac/Liberty/aexpress/backend/orders/services.py) to check the inner `statuscode` inside the SmartParcel JSON response. If `statuscode` is not `"00"`, the request is now treated as a failure and returns `False` along with the descriptive `statusmessage` (e.g. locker unavailable, insufficient balance).
- **Locker Delivery Creation Service**: Simplified and fortified error handling in `process_parcel_delivery` within [services.py](file:///Users/mac/Liberty/aexpress/backend/orders/services.py) and `SmartParcelCreateParcelView` within [views.py](file:///Users/mac/Liberty/aexpress/backend/orders/views.py) to raise `ServiceException` when the underlying locker creation fails.
- **Unit Tests**: Added integration tests to verify successful and failed parcel creation behavior.

---

# [2026-07-14] — Autocomplete Coordinates Bypass

### Frontend
#### Improved
- **Autocomplete Coordinate Bypass**: Updated the shared `AddressAutocompleteInput.tsx`, inline `AddressAutocompleteInput` in `page.tsx`, and `MapPickerModal.tsx` components to check for coordinates (`lat` and `lng`) directly on the selected autocomplete suggestion. When coordinates are present, the frontend bypasses details lookup (geocoding), checks boundaries, and updates states/fires callbacks directly, reducing unnecessary API requests.
- **Inline Component Synchronization**: Corrected the inline `AddressAutocompleteInput` component in the main dashboard `page.tsx` to properly destructure and execute the `onSelect` prop when suggestions are chosen, and added standard details lookup fallback logic.

---

# [2026-07-13] — Mapbox Autocomplete Integration

### Backend
#### Added
- **Mapbox Geocoding v6 API integration**: Switched from Mapbox Search Box Suggest to the Geocoding v6 API forward search (`/search/geocode/v6/forward`) with `autocomplete=true` to fetch suggestions and geographic coordinates (`lat`/`lng`) in a single request.
- **Mapbox Autocomplete Support**: Integrated Mapbox autocomplete into `PlacesAutocompleteView` with support for session tokens.
- **Mapbox Place Details Support**: Updated `PlaceDetailsView` to retrieve feature details from Mapbox using prefix `mapbox:` and session tokens.
- **Fallback Chain**: Configured autocomplete to use Geoapify first, falling back to Mapbox, and finally falling back to AWS Location Service.
- **Autocomplete Coordinates Mapping**: Added support to map and return latitude and longitude coordinates directly in Geoapify and Mapbox autocomplete suggestions if present in the API response.
- **Unit Tests**: Updated integration tests in `orders/test_places.py` to cover Mapbox Geocoding v6 helpers, autocomplete, details, and fallback behaviors.

---

# [2026-07-09] — Google Places Fallback with AWS Location Service


### Backend
#### Added
- **AWS Location Service helpers**: Added AWS Location Service helper functions in `orders/utils.py` (`get_aws_location_client`, `aws_place_autocomplete`, `aws_place_details`, `aws_reverse_geocode`).
- **AWS Place Autocomplete, Details, Reverse Geocode, and Geocode Views**: Added REST API proxy views `PlacesAutocompleteView`, `PlaceDetailsView`, `ReverseGeocodeView`, and `GeocodeView` in `orders/places_views.py` wrapping AWS Location Service.
- **Endpoints routing**: Registered the new proxy endpoints in `orders/urls.py`.
- **AWS Places integration tests**: Added `orders/test_places.py` to cover helpers, proxy views, and geocoding fallbacks.

#### Fixed
- **Geocoding graceful degradation fallback**: Modified `geocode_address` in `orders/utils.py` to fall back to AWS Location Service geocoding if Google Maps Geocoding API fails or throws an exception.

### Frontend
#### Added
- **AWS Places API client calls**: Added backend proxy client endpoints (`PlacesAPI.autocomplete`, `PlacesAPI.details`, `PlacesAPI.reverseGeocode`, `PlacesAPI.geocode`) to `frontend/src/lib/api.ts`.
- **Address Autocomplete AWS Fallback**: Integrated AWS Location Service fallback in `AddressAutocompleteInput.tsx` and the dashboard page's inline `AddressAutocompleteInput` to handle autocomplete queries and details resolution when Google Maps fails or times out.
- **Map Picker AWS Fallback**: Integrated AWS Location Service fallback in `MapPickerModal.tsx` for place autocomplete, details resolution, and reverse geocoding on coordinates.
- **Geocoding Coords Fallback**: Configured `geocodeAddress` utility in both the dashboard and shared `NewOrderScreen` components to fallback to `API.Places.geocode` backend proxy when client-side Google geocoder fails, preventing raw string addresses in fare calculation payloads.

---

# [2026-07-07] — Fix SmartParcel Locker Data Integration

### Backend
#### Fixed
- **Sender Phone Number Lookup Typo**: Fixed typo in `QuickSendView.post()` dictionary lookup key for the sender's phone number (`"sender _phone"` -> `"sender_phone"`), which caused it to always map to an empty string.

#### Added
- **SmartParcel Locker Integration Tests**: Created `orders/test_quick_send_smart_parcel.py` unit test to verify integrated Quick Send order placement with locker details.

### Frontend
#### Fixed
- **SmartParcel Locker Data Propagation**: Added locker delivery and pickup fields (`is_pickup_percel`, `isdelivery_percel`, `collect_code`, `box_id`, `locker_size_id`) to the `apiPayload` mapped object in `dashboard/page.tsx`'s `onPlaceOrder()`.
- **New Order Page Payload Mapping**: Restructured payload creation on the standalone `/new-order` page (`new-order/page.tsx`) to map all camelCase keys to backend-aligned snake_case equivalent fields and include locker data.

---

# [2026-06-04] — Fix Admin Charge Change Page Timeout

### Backend (Admin)
#### Fixed
- **Order representation N+1 query optimization**: Optimized the `Order` model's `__str__` method to return only the order number (`f"Order {self.order_number}"`), avoiding heavy database query loops on related user objects when rendering list choices.
- **Admin models raw_id_fields optimization**: Added `raw_id_fields` to foreign key relationships in all `wallet` and `orders` admin modules (`ChargeAdmin`, `WalletAdmin`, `TransactionAdmin`, `VirtualAccountAdmin`, `WebhookLogAdmin`, `AmortizationWalletAdmin`, `AmortizationTransactionAdmin`, `AmortizationVirtualAccountAdmin`, `OrderAdmin`, `DeliveryAdmin`, `OrderLegAdmin`, `MerchantPricingOverrideAdmin`, `MerchantPriceListAdmin`, `MerchantPriceListItemAdmin`). This completely prevents Django admin from executing N+1 select list queries or rendering massive dropdown lists, fixing the gunicorn timeout crash when displaying admin change pages.

### Backend
#### Added
- **Makefile Update**: Added a `test` target to run the pytest test suite via `.venv/bin/pytest` or system fallback.

---

# [2026-05-20] — Backend Test Suite Failure Resolution

### Backend
#### Added
- **Rider Home Zone Filter**: Implemented home-zone filtering on rider order offers to ensure riders only view jobs that originate from or are routed to their designated zones.
- **Relay Coordinates Validation**: Enforced strict coordinate validation in `create_dispatcher_order` when relay leg generation is requested, raising standard validation errors on missing coordinates.

#### Fixed
- **Rider Wallet Balance Aggregation**: Restored available balance retrieval in `RiderWalletInfoSerializer` to sum the current wallet balance and pending Cash On Delivery (COD) amounts. Queried the `Wallet` model directly to bypass stale in-memory cached relationships.
- **Today's Trips Route Resolution**: Fixed dynamic pattern capturing collision in `riders/urls.py` by re-ordering the `"orders/today/"` pattern before the dynamic `"orders/<str:order_id>/"` pattern, resolving a false "Order not found" 404 response.
- **Wallet Escrow Balance Verification**: Updated escrow tests to force refresh the wallet database state before asserting balances, avoiding stale assert failures.
- **Merchant Subscription Creation Conflicts**: Adjusted subscription test setup to fetch pre-existing model instances automatically spawned by Django signals, preventing unique constraint violations.
- **Proximity Checks Graceful Bypass**: Modified delivery completion views to skip proximity validation checks when geolocation coordinates are omitted from the client payload.
- **Rider Admin Metadata**: Added `short_description` properties to custom model methods in `Rider` model to pass admin view validation checks in the test harness.
- **Rider Duty Switch Standard choices**: Integrated `"online"` and `"offline"` choice options to the `DutyToggleSerializer` class to gracefully bridge mobile app toggle payloads.

---

# [2026-05-19] — Transaction Admin User Phone Search

### Backend (Admin)
#### Added
- **Transaction User Phone Search**: Added user `phone` search field (`wallet__user__phone`) to `TransactionAdmin` to enable administrative users to search/filter wallet transactions by the associated user's phone number.

---

# [2026-05-18] — Amortization Admin Search Bug Fix

### Backend (Admin)
#### Fixed
- **Amortization Admin User Search**: Resolved a Django `FieldError` (unsupported lookup 'full_name') by replacing the invalid Python `@property` lookup with actual database fields (`first_name`, `last_name`, `contact_name`) across `AmortizationWalletAdmin`, `AmortizationTransactionAdmin`, and `AmortizationVirtualAccountAdmin`.
- **Search Robustness**: Standardized user search across amortization admin views to allow querying by first name, last name, or contact name.

---

# [2026-05-16] — Partner Order Count Flexibility

### Frontend (Dispatcher Portal)
#### Changed
- **Number of Orders Flexibility**: Modified the "Number of Orders" input in the Partner Bulk creation flow to accept any integer value.
- **Input Clearing**: Enabled the ability to clear the "Number of Orders" input field during editing for a better user experience.
- **Robust Calculations**: Updated pricing calculations and order submission logic to handle empty or non-numeric input values gracefully.

# [2026-05-15] — Transaction Admin Date Hierarchy

### Backend (Admin)
#### Added
- **Transaction Date Hierarchy**: Added `date_hierarchy` to `TransactionAdmin` for improved date-based navigation and filtering of wallet transactions.
- **Enhanced Search**: Added support for searching transactions by user virtual account number in `TransactionAdmin`.

# [2026-05-12] — Amortization Transaction Admin Enhancements

### Backend (Admin)
#### Added
- **Day Filter**: Added `date_hierarchy` to `AmortizationTransactionAdmin` for better date-based filtering, matching the `OrderAdmin` configuration.

# [2026-05-11] — Multi-Drop Route Visualization

### Frontend (Dispatcher Portal)
#### Added
- **Multi-Drop Map Rendering**: Updated `DeliveryRouteMap` to visualize all delivery stops for `multi` mode orders. Markers are now sequence-numbered, and the route path connects every stop in order.
- **Enhanced Route Details**: The `OrderDetail` sidebar now lists all delivery stops sequentially, showing stop numbers, addresses, status, and receiver contact information.
- **Dynamic Route Indicators**: Implemented a dynamic vertical path indicator in the Route section that scales based on the number of delivery stops.

### API
#### Changed
- **Serializer Expansion**: Updated the dispatcher's `OrderSerializer` to include the nested `deliveries` field, providing full stop data to the frontend.

# [2026-05-08] — Unified Coordinate-Based Routing

### Frontend
#### Added
- **Coordinate Capture**: Enhanced `AddressAutocompleteInput` to capture and return `lat`/`lng` coordinates alongside formatted addresses.
- **Precise Routing**: Integrated coordinate-based inputs into the `bulk-calculate-fare` API calls for Quick, Multi-drop, and Bulk order modes, improving pricing and ETA accuracy.
- **State Management**: Updated `dashboard/page.tsx` to store and manage coordinate data for all delivery stops.

---

# [2026-05-07] — Routing Service Development Environment & Types

### Backend (Routing Service)
#### Added
- **Live Reloading**: Configured `air` for hot-reloading during development.
- **OSRM Types**: Defined `OSRMResponse` and related structs in `types/types.go` for handling map service responses.

#### Fixed
- **Development Tooling**: Resolved "no such tool 'air'" error by properly registering `air` as a Go tool in `go.mod` and adding a `.air.toml` configuration.
- **Multiple Destinations**: Updated the directions endpoint to support multiple destinations via repeated query parameters (`?destinations=p1&destinations=p2`), bypassing semicolon parsing issues in Go 1.17+.


---

# [2026-05-06] — Amortization Wallet & Transactions

### API
#### Added
- **Amortization Wallet**: Implemented `GET /wallet/amortization-wallet/` for riders to view bike hire-purchase progress.
- **Amortization Transactions**: Added `GET /wallet/amortization-transactions/` to retrieve paginated transaction history for the amortization wallet.

---

# [2026-05-05] — Merchant Pricing Override Fix

### API
#### Fixed
- **Merchant Pricing Overrides**: Enabled "upsert" (update or create) behavior for the pricing overrides endpoint by removing the default DRF `UniqueTogetherValidator`, allowing `POST` requests to update existing overrides as originally intended.

---

# [2026-05-04] — Merchant & Dispatcher Cancellation Reason Support

### Frontend (Merchant Dashboard)
#### Fixed
- **Cancellation Reason Visibility**: Fixed an issue where the cancellation reason textarea was not appearing. Optimized modal layout and increased width to prevent clipping.

### Frontend (Dispatcher Portal)
#### Added
- **Enhanced Cancellation Modal**: Redesigned the cancellation modal to always show the reason input field and added "Suggested Reasons" for faster processing.

### API
#### Changed
- **Standardized Responses**: Refactored both Merchant and Dispatcher cancellation endpoints to use `service_response` and `ServiceException` for consistent API behavior.

---

## [2026-04-29] — Multiple Image Upload in Dispatcher Portal

### Frontend
#### Added
- **Multiple Image Selection**: Enhanced the "Create Order" modal to support selecting and uploading multiple images simultaneously.
- **Image Previews**: Added a grid view for uploaded images with the ability to remove individual files before submission.
- **Improved Order Details**: Updated the Order Details view to display all uploaded documents.

#### Changed
- **API Payload**: Updated the dispatcher create order payload to send `file_uploaded_urls` as a list of strings.

## [2026-04-23] — Partner Order Tracking & Management

### Frontend
#### Added
- **Partner Details View**: Integrated a premium partner information card in the Order Detail modal.
- **Document Preview**: Added high-fidelity preview for uploaded proof/waybill documents with full-size viewing support.
- **Processing Metrics Editing**: Enabled inline editing for `Rider Completed` and `Returned` counts for partner bulk orders.
- **Real-time Synchronization**: Added `useEffect` hooks to ensure partner metrics are correctly loaded and reset during order navigation.

### API
#### Added
- **Order Stats Update**: Added `PATCH /dispatch/orders/{order_number}/update-partner-stats/` to update partner processing counts.
- **Serializer Expansion**: Updated `OrderSerializer` to include `is_partner_order`, `partner_order_count`, `day_returned_count`, `rider_completed_count`, and `file_uploaded_url`.
- **Merchant Access Control**: Restricted `MerchantViewSet` list action to `IsDispatcher` permission and other actions to `IsDispatcherAdmin`.

---

## [2026-04-22] — ClickUp Task Logging Automation

### Chore
- **ClickUp Logger**: Implemented a Python script `scripts/clickup_logger.py` to automate task logging to ClickUp.
- **Session Tracking**: Added `.claude/session_log.json` to track and batch-log development tasks.
- **Auto-routing**: Implemented keyword-based routing to automatically assign tasks to the correct ClickUp Lists.

---

## [2026-04-16] — SmartParcel Toggle Fix

### Frontend
#### Fixed
- **SmartParcel Toggle**: Resolved a `TypeError` that occurred when toggling "Deliver to SmartParcel Locker" by ensuring that data fetched from the SmartParcel API is always treated as an array before mapping.
- **Robust Data Fetching**: Updated `useEffect` hooks to correctly extract lists (states, cities, boxes, sizes) from backend responses and added defensive array checks in the render logic.
---

## [2026-04-17] — SmartParcel Integration & Simulation

### API
#### Added
- **SmartParcel Simulation**: Added `simulate/drop/` and `simulate/collect/` endpoints to simulate locker state transitions in sandbox mode for end-to-end testing of the locker workflow.
- **SmartParcel Integration**: Implemented comprehensive suite of endpoints for SmartParcel locker integration:
  - `GET smart-parcel/states/`
  - `GET smart-parcel/states/{id}/cities/`
  - `GET smart-parcel/boxes/city/{id}/`
  - `GET smart-parcel/boxes/assigned/city/{id}/`
  - `GET smart-parcel/locker-sizes/`
  - `POST smart-parcel/parcels/`
  - `GET smart-parcel/parcels/pending-pickups/`
  - `GET smart-parcel/parcels/resolve-collect-code/{code}/`
  - `GET smart-parcel/parcels/{tracking}/`
  - `POST smart-parcel/parcels/{tracking}/cancel/`

### Frontend
#### Added
- **SmartParcel Locker Workflow**: Integrated SmartParcel locker selection and collect code resolution directly into the Order Creation flow in the dashboard.
- **Defensive guards**: Added defensive null guards for SmartParcel data arrays to prevent runtime crashes during API latency or failures.

## [2026-04-02] — Order Mode Redesign & Grouped Pricing Fix


### Frontend
#### Changed
- **Order Mode Selector**: Redesigned the "Quick vs Grouped" sub-mode selection from a standard dropdown to modern, interactive cards with icons and premium aesthetics.
- **Grouped Pricing Fix**: Resolved a bug where "Grouped Order" failed to trigger route calculation and estimation.
- **Payload Fix**: Ensured the `mode` field ("quick" or "grouped") is correctly included in the API payload when placing an order.
- **Estimated Prices**: Optimized the dynamic pricing logic to correctly apply the 30% discount to both simple and tiered pricing models in "Grouped" mode.

---

## [2026-03-27] — Checkout Referral & Virtual Account Integration

### Frontend
#### Added
- **Signup Referral:** Added an optional "Referral Code" field to Step 1 of the merchant signup form.
- **Dynamic Wallet Funding:** Integrated `getVirtualAccount` API to fetch real bank details for wallet funding via bank transfer.
- **Subscription Management:** Added a new "Subscription" sidebar item and management screen for plan selection.
- **Subscription Enhancements:** Refactored sidebar to a nested "Subscription" menu with "Plan" and "Invoice" sub-items.
- **Postpaid Plans:** Added support for Postpaid subscription plans with a multi-tab interface in the Subscription screen.
- **Invoices Screen:** Implemented a dedicated screen for viewing and downloading subscription invoices.
- **API Wrapper:** Added `Wallet.getVirtualAccount()`, `SubscriptionAPI`, and Postpaid methods to `src/lib/api.ts`.

#### Changed
- Updated signup payload to include `referral_code`.
- Improved professional UI for referral input with a "Gift" icon.

### API
#### Added
- `GET /wallet/virtual-account/` — Retrieves or creates a dedicated virtual account for the merchant.
- `GET /subscriptions/plans/` — Retrieves available subscription plans.
- `POST /subscriptions/plans/{id}/subscribe/` — Subscribes a merchant to a plan.
- `GET /subscriptions/postpaid/plans/` — Retrieves available postpaid plans.
- `POST /subscriptions/postpaid/plans/{id}/activate/` — Activates a postpaid plan for a merchant.
- `GET /subscriptions/postpaid/active/` — Retrieves the current active postpaid subscription.
