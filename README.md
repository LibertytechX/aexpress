# AXpress (Assured Express)

[![Assure Express Logo](frontend/public/logo/logo1.png)](https://www.axpress.net)

**AXpress** is a next-generation logistics and delivery platform designed for merchants in Lagos, Nigeria. It provides a comprehensive ecosystem for managing deliveries, tracking riders in real-time, and scaling logistics operations through automated zone management and AI-driven intelligence.

---

## 🚀 Project Overview

AXpress bridges the gap between merchants and dispatchers with a unified platform. It features a robust **Django/FastAPI Backend**, a premium **Next.js Merchant Dashboard**, and a high-performance **Vite-based Dispatcher Portal**.

### Core Value Propositions:
- **Scalability:** Optimized for local and multi-zone delivery operations.
- **Intelligence:** Integrated with Google Cloud Vertex AI and Gemini for smarter logistics.
- **Real-time:** Live rider tracking and order updates powered by Ably.
- **Financial Integration:** Built-in wallet systems with virtual account funding and flexible subscription plans (Prepaid/Postpaid).

---

## 🛠 Project Structure

This repository is managed as a monorepo:

- **[`backend/`](backend/)**: Django 4.2 + DRF & FastAPI. Handles core logic, order routing, and AI integrations.
- **[`frontend/`](frontend/)**: Next.js 16 + React 19 Merchant Portal. Focuses on premium merchant UX/UI.
- **[`dispatcher-frontend/`](dispatcher-frontend/)**: Vite + React 19 Operations Dashboard for real-time fleet management.
- **[`functions/`](functions/)**: Serverless functions for extended backend capabilities.

---

## 🏗 Tech Stack

### Backend (Python)
- **Frameworks:** [Django 4.2](https://www.djangoproject.com/), [Django REST Framework](https://www.django-rest-framework.org/), [FastAPI](https://fastapi.tiangolo.com/)
- **Primary DB:** [PostgreSQL](https://www.postgresql.org/)
- **Cache/Broker:** [Redis](https://redis.io/)
- **Task Queue:** [Celery](https://docs.celeryq.dev/)
- **AI/ML:** [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai), [Google GenAI (Gemini)](https://ai.google.dev/)
- **Real-time:** [Ably](https://ably.com/)

### Merchant Frontend (TypeScript)
- **Framework:** [Next.js 16](https://nextjs.org/) (App Router)
- **Library:** [React 19](https://react.dev/)
- **Styling:** [Tailwind CSS 4](https://tailwindcss.com/)
- **Animations:** [Framer Motion](https://www.framer.com/motion/)
- **State/Real-time:** Ably SDK

### Dispatcher Portal (JavaScript)
- **Tooling:** [Vite](https://vitejs.dev/)
- **Library:** [React 19](https://react.dev/)
- **Real-time:** Ably SDK

---

## 🚦 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL & Redis

### 1. Backend Setup
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

### 2. Frontend Setup (Merchant)
```bash
cd frontend
npm install
npm run dev
```

### 3. Dispatcher Setup
```bash
cd dispatcher-frontend
npm install
npm run dev
```

---

## 🧪 Seeding & Development

AXpress requires several data layers (Vehicles, Zones, Verticals) to function correctly.

### Initial Data Seeding:
```bash
python manage.py seed_vehicles                 # Vehicle types & pricing
python manage.py seed_verticals_and_zones      # Geographic delivery zones
python manage.py populate_users                # Test roles
python manage.py seed_occ_test_data            # OCC components (Captains, Targets)
```

### Background Tasks:
```bash
celery -A ax_merchant_api worker -l info
celery -A ax_merchant_api beat -l info
```

---

## 📖 Documentation & Standards

- **[API Endpoints](ENDPOINTS_DOCUMENTATION.md):** Full reference for all REST endpoints and webhooks.
- **[Development Rules](GEMINI.md):** Mandatory coding standards and API patterns.
- **[Changelog](CHANGELOG.md):** History of features and bug fixes.

---

## 🔐 Authentication Modes

1.  **JWT (Simple JWT):** Used by Merchants and Riders for standard platform access.
2.  **Service API Keys:** Scoped, SHA-256 hashed keys for server-to-server communication (e.g., OCC to Backend).

---

© 2026 Assured Express. All rights reserved.
