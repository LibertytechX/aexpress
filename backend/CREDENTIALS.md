# AX Merchant Portal - Credentials & Access

## 🌐 Application URLs

### Backend (Django)
- **API Base URL:** http://127.0.0.1:8000/api/
- **Django Admin:** http://127.0.0.1:8000/admin/
- **Server Status:** Running ✅

### Frontend (React)
- **Application URL:** http://localhost:9000/index.html
- **Server Status:** Running ✅

---

## 🔐 Superuser Credentials (Django Admin)

**Access Django Admin Panel:**
- **URL:** http://127.0.0.1:8000/admin/
- **Phone:** `08099999999`
- **Password:** `admin123`
- **Email:** admin@axpress.com
- **Business Name:** AX Express Admin

---

## 🗄️ Database Credentials

### PostgreSQL
- **Host:** localhost
- **Port:** 5432
- **Database:** axpress
- **User:** postgres
- **Password:** 19sedimat54

**Connection String:**
```
postgresql://postgres:19sedimat54@localhost:5432/axpress
```

---

## 📦 Redis Configuration

- **Host:** localhost
- **Port:** 6379
- **Database:** 1 (for cache)

---

## 🧪 Test User Account

A test merchant account was created during API testing:

- **Phone:** `08012345678`
- **Password:** `testpass123`
- **Email:** test@testlogistics.com
- **Business Name:** Updated Logistics Ltd
- **Contact Name:** John Doe

You can use this account to test the API or login to the frontend.

---

## 🔑 JWT Token Configuration

- **Access Token Lifetime:** 24 hours
- **Refresh Token Lifetime:** 168 hours (7 days)
- **Algorithm:** HS256
- **Token Type:** Bearer

---

## 📡 API Endpoints Quick Reference

### Authentication
```
POST   /api/auth/signup/      - Register new merchant
POST   /api/auth/login/       - Login with phone + password
POST   /api/auth/logout/      - Logout (blacklist token)
POST   /api/auth/refresh/     - Refresh access token
GET    /api/auth/me/          - Get current user profile
PUT    /api/auth/profile/     - Update user profile
```

---

## 🚀 Quick Start Commands

### Start Backend Server
```bash
cd backend
source venv/bin/activate
python manage.py runserver 8000
```

### Start Frontend Server
```bash
# Already running on port 9000
# If needed to restart:
npx http-server -p 9000
```

### Run API Tests
```bash
cd backend
source venv/bin/activate
python test_auth_api.py
```

### Create Another Superuser
```bash
cd backend
source venv/bin/activate
python create_superuser.py
```

### Access Django Shell
```bash
cd backend
source venv/bin/activate
python manage.py shell
```

### Run Database Migrations
```bash
cd backend
source venv/bin/activate
python manage.py makemigrations
python manage.py migrate
```

---

## 🔒 Security Notes

⚠️ **IMPORTANT:** These are development credentials. 

**Before deploying to production:**
1. Change all passwords
2. Update `SECRET_KEY` in `.env`
3. Set `DEBUG=False`
4. Update `ALLOWED_HOSTS`
5. Use environment variables for sensitive data
6. Enable HTTPS
7. Configure proper CORS origins
8. Set up proper database backups

---

## 📞 Admin Panel Features

Once logged into Django Admin (http://127.0.0.1:8000/admin/), you can:

- ✅ View all registered users
- ✅ Create/edit/delete user accounts
- ✅ Activate/deactivate accounts
- ✅ Verify email/phone status
- ✅ View user login history
- ✅ Manage user permissions
- ✅ View blacklisted tokens
- ✅ Monitor outstanding tokens

---

## 🎯 What's Next?

Now that you have admin access, you can:

1. **Monitor Users:** View all registered merchants
2. **Manage Accounts:** Activate/deactivate accounts as needed
3. **Test Authentication:** Use the test account to verify login flow
4. **Build Phase 2:** Continue with Wallet System implementation

---

**Last Updated:** February 14, 2026  
**Status:** Phase 1 Authentication - COMPLETE ✅

