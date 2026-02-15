# AX Merchant Portal - Django Backend

## 🎉 Phase 1: Authentication & Order Management - COMPLETED ✅

This is the Django backend for the AX Merchant Portal, a package delivery service platform for merchants in Lagos, Nigeria.

---

## 📋 Project Structure

```
backend/
├── ax_merchant_api/          # Django project settings
│   ├── settings.py           # Main configuration
│   ├── urls.py               # URL routing
│   └── wsgi.py               # WSGI application
├── authentication/           # Authentication app
│   ├── models.py             # Custom User model
│   ├── serializers.py        # DRF serializers
│   ├── views.py              # API views
│   ├── urls.py               # Authentication URLs
│   └── admin.py              # Admin configuration
├── orders/                   # Order Management app
│   ├── models.py             # Order, Delivery, Vehicle models
│   ├── serializers.py        # Order serializers
│   ├── views.py              # Order API views
│   ├── urls.py               # Order URLs
│   ├── admin.py              # Order admin configuration
│   └── management/           # Management commands
│       └── commands/
│           └── seed_vehicles.py  # Seed vehicle data
├── .env                      # Environment variables
├── requirements.txt          # Python dependencies
├── manage.py                 # Django management script
├── test_auth_api.py          # Authentication API test script
├── test_orders_api.py        # Order Management API test script
├── API_DOCUMENTATION.md      # Authentication API docs
└── README.md                 # This file
```

---

## 🚀 Getting Started

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
   Edit `.env` file with your settings (already configured)

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Seed initial data:**
   ```bash
   python manage.py seed_vehicles
   ```

6. **Start development server:**
   ```bash
   python manage.py runserver 8000
   ```

7. **Test the APIs:**
   ```bash
   python test_auth_api.py
   python test_orders_api.py
   ```

---

## 🔧 Technology Stack

- **Django 4.2.28** - Web framework
- **Django REST Framework 3.16.1** - REST API toolkit
- **PostgreSQL** - Primary database
- **Redis** - Caching and session storage
- **JWT (Simple JWT)** - Token-based authentication
- **CORS Headers** - Cross-origin resource sharing

---

## 📡 API Endpoints

### Authentication
- `POST /api/auth/signup/` - Register new merchant
- `POST /api/auth/login/` - Login with phone + password
- `POST /api/auth/logout/` - Logout (blacklist token)
- `POST /api/auth/refresh/` - Refresh access token
- `GET /api/auth/me/` - Get current user profile
- `PUT /api/auth/profile/` - Update user profile

### Order Management
- `GET /api/orders/vehicles/` - Get available vehicles
- `POST /api/orders/quick-send/` - Create Quick Send order
- `POST /api/orders/multi-drop/` - Create Multi-Drop order
- `POST /api/orders/bulk-import/` - Create Bulk Import order
- `GET /api/orders/` - Get all orders (with filters)
- `GET /api/orders/stats/` - Get order statistics
- `GET /api/orders/<order_number>/` - Get order details

See `API_DOCUMENTATION.md` and `orders/API_DOCUMENTATION.md` for detailed API documentation.

---

## 🗄️ Database Schema

### Users Table
- `id` (UUID) - Primary key
- `business_name` - Merchant business name
- `contact_name` - Contact person name
- `phone` - Phone number (unique, used for login)
- `email` - Email address (unique)
- `address` - Business address
- `is_active` - Account status
- `email_verified` - Email verification status
- `phone_verified` - Phone verification status
- `created_at` - Account creation timestamp
- `updated_at` - Last update timestamp
- `last_login` - Last login timestamp

### Vehicles Table
- `id` (Integer) - Primary key
- `name` - Vehicle type (Bike, Car, Van)
- `max_weight_kg` - Maximum weight capacity
- `base_price` - Base delivery price
- `description` - Vehicle description
- `is_active` - Availability status

### Orders Table
- `id` (UUID) - Primary key
- `order_number` - Unique order number (6XXXXXX format)
- `user_id` (FK) - Reference to merchant
- `mode` - Order mode (quick, multi, bulk)
- `vehicle_id` (FK) - Reference to vehicle
- `pickup_address` - Pickup location
- `sender_name` - Sender name
- `sender_phone` - Sender phone
- `payment_method` - Payment method (wallet, cash_on_pickup, receiver_pays)
- `total_amount` - Total order cost
- `status` - Order status (Pending, Assigned, Started, Done, etc.)
- `created_at` - Order creation timestamp
- `updated_at` - Last update timestamp
- `scheduled_pickup_time` - Scheduled pickup time (optional)
- `notes` - Order notes

### Deliveries Table
- `id` (UUID) - Primary key
- `order_id` (FK) - Reference to order
- `dropoff_address` - Delivery destination
- `receiver_name` - Receiver name
- `receiver_phone` - Receiver phone
- `package_type` - Package type (Box, Envelope, Fragile, etc.)
- `notes` - Delivery notes
- `status` - Delivery status (Pending, InTransit, Delivered, etc.)
- `sequence` - Delivery sequence number (for multi-drop)
- `created_at` - Delivery creation timestamp
- `delivered_at` - Delivery completion timestamp

---

## 🔐 Authentication Flow

1. **Signup:** User registers with business details → Receives JWT tokens
2. **Login:** User logs in with phone + password → Receives JWT tokens
3. **Access Protected Routes:** Include `Authorization: Bearer <access_token>` header
4. **Token Refresh:** When access token expires, use refresh token to get new one
5. **Logout:** Blacklist refresh token to invalidate session

---

## ✅ Phase 1 Completed Features

### Authentication (Feature 1) ✅
- ✅ Custom User model with UUID primary key
- ✅ User registration (signup)
- ✅ User login with phone + password
- ✅ JWT token generation (access + refresh)
- ✅ Token refresh endpoint
- ✅ User profile retrieval
- ✅ User profile update
- ✅ Logout with token blacklisting
- ✅ PostgreSQL database integration
- ✅ Redis caching setup
- ✅ CORS configuration for frontend
- ✅ Django admin panel integration
- ✅ API testing script

### Order Management (Feature 3) ✅
- ✅ Vehicle model with pricing (Bike: ₦1,200, Car: ₦4,500, Van: ₦12,000)
- ✅ Order model with auto-generated order numbers
- ✅ Delivery model for multi-drop support
- ✅ Quick Send order creation (single delivery)
- ✅ Multi-Drop order creation (multiple deliveries)
- ✅ Bulk Import order creation (CSV/text/OCR support)
- ✅ Order listing with filtering (status, mode, limit)
- ✅ Order detail retrieval by order number
- ✅ Order statistics for dashboard
- ✅ Vehicle listing endpoint
- ✅ Django admin integration for orders
- ✅ Management command to seed vehicle data
- ✅ Comprehensive API testing script

---

## 📝 Environment Variables

```env
# Django Settings
SECRET_KEY=<your-secret-key>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=axpress
DB_USER=postgres
DB_PASSWORD=19sedimat54
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT Configuration
JWT_ACCESS_TOKEN_LIFETIME=24    # hours
JWT_REFRESH_TOKEN_LIFETIME=168  # hours (7 days)

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:9000
```

---

## 🧪 Testing

### Authentication API Tests
Run the automated authentication API test script:
```bash
python test_auth_api.py
```

This will test:
- User signup
- User login
- Get profile
- Update profile
- Token refresh
- Logout

### Order Management API Tests
Run the automated order management API test script:
```bash
python test_orders_api.py
```

This will test:
- Login and authentication
- Get available vehicles
- Create Quick Send order
- Create Multi-Drop order (3 deliveries)
- Create Bulk Import order (5 deliveries)
- Get all orders
- Get order statistics
- Get specific order details

---

## 📦 Next Steps (Remaining Phase 1 Features)

1. **Wallet System (Feature 2)** - PENDING
   - Create Wallet model
   - Paystack integration for funding
   - Transaction history
   - Balance management
   - Wallet deduction on order creation
   - Wallet funding endpoints

2. **Dashboard (Feature 4)** - PARTIALLY COMPLETE
   - ✅ Order statistics endpoint (already implemented)
   - ⏳ Wallet balance display
   - ⏳ Recent transactions
   - ⏳ Quick actions

---

## 🚀 Deployment

### Local Development
- Backend: `http://127.0.0.1:8000`
- Frontend: `http://localhost:9000`

### Production (Planned)
- **Backend:** Digital Ocean
- **Frontend:** Vercel
- **Database:** PostgreSQL (Digital Ocean)
- **Cache:** Redis (Digital Ocean)

---

## 📞 Support

For issues or questions, refer to:
- `API_DOCUMENTATION.md` - Complete API reference
- `../frontend/BACKEND_REQUIREMENTS.md` - Full backend requirements
- `../frontend/FEATURE_SUMMARY.md` - Feature breakdown

---

**Status:** ✅ Phase 1 Authentication & Order Management - COMPLETE
**Server:** Running on http://127.0.0.1:8000
**Last Updated:** February 14, 2026

---

## 🎯 Order Management Features

### Three Delivery Modes:
1. **Quick Send** - Single pickup, single delivery
2. **Multi-Drop** - Single pickup, multiple deliveries
3. **Bulk Import** - Single pickup, multiple deliveries (from CSV/text/OCR)

### Vehicle Types & Pricing:
- **Bike**: ₦1,200 (max 10kg)
- **Car**: ₦4,500 (max 70kg)
- **Van**: ₦12,000 (max 600kg)

### Payment Methods:
- **Wallet**: Prepaid wallet balance (auto-debit)
- **Cash on Pickup**: Pay rider at pickup
- **Receiver Pays**: Cash on delivery (COD)

### Order Status Flow:
```
Pending → Assigned → Started → Done
         ↓
    CustomerCanceled / RiderCanceled / Failed
```

