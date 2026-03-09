# AXpress Backend

This is the Django backend for AXpress, a package delivery service platform for merchants in Lagos, Nigeria. It powers the Merchant Portal, Rider App, and the Operations Command Center (OCC).

---

## Project Structure

```
backend/
├── ax_merchant_api/          # Django project settings
│   ├── settings.py           # Main configuration
│   ├── urls.py               # URL routing
│   ├── celery.py             # Celery app configuration
│   └── wsgi.py               # WSGI application
├── authentication/           # Authentication app
│   ├── models.py             # Custom User model (with user types)
│   ├── serializers.py        # DRF serializers
│   ├── views.py              # API views
│   └── urls.py               # Authentication URLs
├── orders/                   # Order Management app
│   ├── models.py             # Order, Delivery, Vehicle, OrderLeg models
│   ├── serializers.py        # Order serializers
│   ├── views.py              # Order API views
│   └── urls.py               # Order URLs
├── dispatcher/               # Dispatch & Operations app
│   ├── models.py             # Rider, Merchant, Zone, Vertical, VehicleAsset,
│   │                         #   ServiceAPIKey, RiderDutyLog, snapshots, etc.
│   ├── views.py              # Rider/Zone/Vertical ViewSets
│   ├── urls.py               # Dispatcher URLs (/api/dispatch/)
│   ├── authentication.py     # ServiceAPIKeyAuthentication (server-to-server)
│   ├── permissions.py        # HasOCCReadScope, HasOCCWriteScope
│   ├── occ_views.py          # OCC analytics endpoints (12 views)
│   ├── occ_urls.py           # OCC URL routing (/api/occ/)
│   ├── tasks.py              # Celery tasks (snapshots, ghost riders, etc.)
│   ├── serializers.py        # Dispatcher serializers
│   ├── admin.py              # Admin configuration
│   └── management/commands/
│       └── create_service_key.py  # Generate service API keys
├── riders/                   # Rider-specific app
│   ├── models.py             # OrderOffer model
│   ├── tasks.py              # Rider Celery tasks
│   └── urls.py               # Rider URLs
├── wallet/                   # Wallet & payments app
├── webhooks/                 # Webhook delivery app
├── bot/                      # Bot integration app
├── referrals/                # Referral system app
├── requirements.txt          # Python dependencies
└── manage.py                 # Django management script
```

---

## Getting Started

### Prerequisites
- Python 3.9+
- PostgreSQL (running on port 5432)
- Redis (running on port 6379)

### Installation

1. **Activate virtual environment:**
   ```bash
   cd backend
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Copy `.env.example` to `.env` and fill in your settings.

4. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Seed initial data:**
   ```bash
   python manage.py seed_vehicles
   python manage.py seed_verticals_and_zones
   python manage.py populate_users
   ```

6. **Seed OCC test data** (optional — populates zone captains, vertical leads, duty logs, snapshots, ratings, and zone targets):
   ```bash
   python manage.py seed_occ_test_data
   ```

7. **Start development server:**
   ```bash
   python manage.py runserver 8000
   ```

8. **Start Celery worker + beat (for background tasks):**
   ```bash
   celery -A ax_merchant_api worker -l info
   celery -A ax_merchant_api beat -l info
   ```

---

## Technology Stack

- **Django 4.2** - Web framework
- **Django REST Framework** - REST API toolkit
- **PostgreSQL** - Primary database
- **Redis** - Celery broker, caching, and session storage
- **Celery** - Async task queue and periodic beat scheduler
- **JWT (Simple JWT)** - Token-based authentication (merchants, riders)
- **Service API Keys** - Server-to-server authentication (OCC)
- **CORS Headers** - Cross-origin resource sharing

---

## API Endpoints

### Authentication (`/api/auth/`)
- `POST /signup/` - Register new merchant
- `POST /login/` - Login with phone + password
- `POST /logout/` - Logout (blacklist token)
- `POST /refresh/` - Refresh access token
- `GET /me/` - Get current user profile
- `PUT /profile/` - Update user profile

### Orders (`/api/orders/`)
- `GET /vehicles/` - Get available vehicles
- `POST /quick-send/` - Create Quick Send order
- `POST /multi-drop/` - Create Multi-Drop order
- `POST /bulk-import/` - Create Bulk Import order
- `GET /` - List orders (with filters)
- `GET /stats/` - Order statistics
- `GET /<order_number>/` - Order details

### Dispatch (`/api/dispatch/`)
- Rider CRUD + `toggle_duty`, `update_location`
- Zone CRUD
- Vertical CRUD (`/verticals/`)
- VehicleAsset management
- Relay node management
- Activity feed

### OCC Analytics (`/api/occ/`) — Service API Key auth
- `GET /verticals/` - All verticals with aggregated metrics
- `GET /verticals/<id>/` - Single vertical detail
- `GET /verticals/<id>/zones/` - Zones under a vertical
- `GET /zones/<id>/dashboard/` - Zone dashboard (orders, revenue, riders, merchants)
- `GET /zones/<id>/riders/` - Riders in a zone with performance metrics
- `GET /zones/<id>/merchants/` - Merchants in a zone with analytics
- `GET /riders/<id>/performance/` - Individual rider performance
- `GET /riders/locations/` - Real-time rider GPS positions
- `GET /merchants/<id>/analytics/` - Individual merchant analytics
- `GET /leaderboard/zones/` - Zone leaderboard with salary calculations
- `GET /leaderboard/verticals/` - Vertical leaderboard with salary calculations
- `GET /orders/analytics/` - Platform-wide order analytics

All OCC endpoints accept a `?period=` query param: `today`, `this_week`, `past_7_days`, `this_month`, `last_month`, `this_year`, or `YYYY-MM`.

### Other
- `/api/wallet/` - Wallet & Paystack integration
- `/api/riders/` - Rider-specific endpoints
- `/api/webhooks/` - Webhook delivery
- `/api/bot/` - Bot integration
- `/api/riders/referrals/` - Referral system

---

## Authentication

### Merchant / Rider Auth (JWT)
1. Register or login to receive JWT access + refresh tokens
2. Include `Authorization: Bearer <access_token>` on protected routes
3. Refresh tokens when expired, blacklist on logout

### OCC Server-to-Server Auth (Service API Key)
1. Generate a key: `python manage.py create_service_key "OCC Production" --scopes occ:read occ:write`
2. The raw `sk_...` key is displayed once — store it securely in the OCC backend's environment
3. OCC calls include `Authorization: Bearer sk_...` header
4. Keys are SHA-256 hashed at rest; scoped permissions control access

---

## Celery Beat Schedule

| Task | Schedule | Description |
|------|----------|-------------|
| `riders.tasks.publish_random_order_offer` | Every minute | Publish pending order offers to riders |
| `webhooks.tasks.webhook_retry_cron` | Every 30 seconds | Retry failed webhook deliveries |
| `dispatcher.tasks.aggregate_daily_rider_snapshots` | Daily 00:05 | Pre-aggregate rider metrics into snapshot table |
| `dispatcher.tasks.aggregate_daily_merchant_snapshots` | Daily 00:10 | Pre-aggregate merchant metrics into snapshot table |
| `dispatcher.tasks.update_merchant_activity_status` | Every 6 hours | Classify merchants as active/watch/inactive |
| `dispatcher.tasks.flag_ghost_riders` | Every 15 minutes | Detect offline riders with GPS movement |

---

## Key Models

| Model | App | Purpose |
|-------|-----|---------|
| `User` | authentication | Custom user with UUID PK, user types (Merchant, Rider, ZoneCaptain, VerticalLead) |
| `Order` | orders | Delivery orders with status flow, payment, and routing |
| `Delivery` | orders | Individual drop-off within an order |
| `OrderLeg` | orders | Relay leg for long-distance multi-hop deliveries |
| `Rider` | dispatcher | Rider profile, GPS, duty status, vehicle assignment |
| `Merchant` | dispatcher | Merchant profile, zone assignment, activity status |
| `Vertical` | dispatcher | Organizational unit grouping multiple zones |
| `Zone` | dispatcher | Geographic delivery zone with center point + radius |
| `VehicleAsset` | dispatcher | Physical vehicle with GPS telemetry |
| `ServiceAPIKey` | dispatcher | SHA-256 hashed API keys for server-to-server auth |
| `RiderDutyLog` | dispatcher | On/off duty transitions for peak-hour analysis |
| `RiderDailySnapshot` | dispatcher | Pre-aggregated daily rider metrics |
| `MerchantDailySnapshot` | dispatcher | Pre-aggregated daily merchant metrics |
| `DeliveryRating` | dispatcher | Per-delivery CSAT rating |
| `ZoneTarget` | dispatcher | Monthly KPI targets per zone |
| `ZoneCaptain` | dispatcher | Zone captain assignment and salary structure |
| `VerticalLead` | dispatcher | Vertical lead assignment and salary structure |

---

## Management Commands

| Command | Description |
|---------|-------------|
| `seed_vehicles` | Seed vehicle types (Bike, Car, Van) with pricing |
| `seed_verticals_and_zones` | Seed 4 verticals and 20 Lagos zones with coordinates |
| `populate_users` | Create test merchants and riders |
| `seed_occ_test_data` | Seed all OCC tables: zone captains, vertical leads, zone targets, duty logs, rider/merchant daily snapshots, delivery ratings. Requires the 3 commands above to run first |
| `create_service_key` | Generate a service API key for server-to-server auth (e.g. OCC) |
| `seed_relay_network` | Seed relay nodes and riders across zones |
| `populate_mock_orders` | Create mock orders for testing |

### Seeding order for a fresh database

```bash
python manage.py seed_vehicles
python manage.py seed_verticals_and_zones
python manage.py populate_users
python manage.py populate_mock_orders
python manage.py seed_occ_test_data
python manage.py create_service_key "OCC Dev" --scopes occ:read occ:write
```

---

## Order Status Flow

```
Pending -> Assigned -> Started -> Pickup -> Fulfilling -> Arrived -> Done
            |
            v
  CustomerCanceled / RiderCanceled / Failed
```

---

## Deployment

### Local Development
- Backend: `http://127.0.0.1:8000`
- Frontend: `http://localhost:9000`

### Production
- **Backend:** Digital Ocean
- **Frontend:** Vercel
- **Database:** PostgreSQL (Digital Ocean)
- **Cache/Broker:** Redis (Digital Ocean)

