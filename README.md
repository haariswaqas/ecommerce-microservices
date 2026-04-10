# Bazar — E-Commerce Microservices Platform

A production-style e-commerce backend built with Django REST Framework, following microservices architecture principles. Three independent services communicate over HTTP and RabbitMQ, each owning its own database.

---

## Services

| Service | Port | Responsibility |
|---|---|---|
| **User Service** | 8001 | Registration, login, JWT issuance, profiles |
| **Product Service** | 8002 | Product catalogue, stock management |
| **Order Service** | 8003 | Order creation, stock reservation, order history |
| **Nginx** | 80 | API gateway — routing, rate limiting, security |

---

## Tech Stack

- **Framework** — Django 5.0 + Django REST Framework
- **Auth** — JWT via `djangorestframework-simplejwt`
- **Databases** — PostgreSQL 16 (one per service)
- **Message Broker** — RabbitMQ 3.13
- **Cache** — Redis 7
- **Gateway** — Nginx
- **Containerization** — Docker + Docker Compose
- **WSGI** — Gunicorn

---

## Architecture Overview

```
Client (Postman / Browser)
        │
        ▼
  ┌─────────────┐
  │    Nginx    │  ← Rate limiting, routing, blocks /internal/ routes
  └──────┬──────┘
         │
   ┌─────┼──────────────┐
   ▼     ▼              ▼
User   Product        Order
Service Service       Service
   │     │              │
   ▼     ▼              ▼
users  products       orders
  DB     DB             DB

         └─── RabbitMQ ───┘  (async events)
         └─── Redis      ───┘  (cache/sessions)
```

Each service is completely independent. No shared databases. No cross-service foreign keys. Services communicate via HTTP (synchronous) or RabbitMQ (asynchronous).

---

## Key Design Decisions

### JWT with embedded claims
The User Service embeds `user_id`, `role`, `email`, and `first_name` directly into the JWT payload. Other services decode the token without hitting any database — fully stateless authentication.

### No cross-service foreign keys
Products store `created_by` as a plain `UUIDField`, not a FK to the user table. Orders store `user_id` and `product_id` as UUIDs. This is intentional — microservices never share database schemas.

### Server-side pricing
When a customer places an order, the Order Service fetches the current product price from the Product Service. The client sends only `product_id` and `quantity` — prices cannot be manipulated client-side.

### Internal secret for service-to-service calls
Internal endpoints (`/internal/`) are protected by a shared `X-Internal-Secret` header, not JWT. Nginx blocks all `/internal/` routes from public access. `hmac.compare_digest` is used for timing-safe comparison.

### Role-based access
- **Customers** — browse products, place orders, cancel their own orders
- **Sellers** — manage their own products, view orders containing their products
- **Admins** — full access across all resources

---

## Getting Started

### Prerequisites
- Docker
- Docker Compose

### Setup

```bash
# Clone the repo
git clone <repo-url>
cd bazar

# Copy and configure environment variables
cp .env.example .env

# Build and start all services
docker compose up --build -d

# Run migrations
docker exec -it user_service python manage.py migrate
docker exec -it product_service python manage.py migrate
docker exec -it order_service python manage.py migrate

# Create a superuser (optional)
docker exec -it user_service python manage.py createsuperuser
```

### Verify everything is running

```bash
curl http://localhost/health
# {"status":"ok"}
```

---

## API Reference

All requests go through `http://localhost` (Nginx on port 80).

### Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/users/register/` | None | Register a new user |
| POST | `/api/users/login/` | None | Login, returns JWT tokens |
| POST | `/api/users/token/refresh/` | None | Refresh access token |
| GET/PATCH | `/api/users/profile/` | Bearer token | View or update your profile |

### Products

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/products/` | None | List all active products |
| GET | `/api/products/{id}/` | None | Get product details |
| POST | `/api/products/` | Seller JWT | Create a product |
| PATCH | `/api/products/{id}/` | Seller JWT (owner) | Update your product |
| DELETE | `/api/products/{id}/` | Seller JWT (owner) | Deactivate your product |

Supports filtering by `?category=electronics`, search via `?search=`, and ordering via `?ordering=price`.

### Orders

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/orders/orders/` | Bearer token | List your orders |
| POST | `/api/orders/orders/` | Customer JWT | Place a new order |
| GET | `/api/orders/orders/{id}/` | Bearer token | Get order details |
| POST | `/api/orders/orders/{id}/cancel/` | Customer JWT (owner) | Cancel a pending order |

### Example — Place an Order

```json
POST /api/orders/orders/
Authorization: Bearer <customer_token>

{
  "items": [
    { "product_id": "e0580954-bc76-4540-bf27-fb7915a3c28c", "quantity": 2 },
    { "product_id": "fcd74aba-1279-4ac3-877a-dbd12c2111b1", "quantity": 1 }
  ],
  "shipping_address": "123 Main Street, New York, NY 10001",
  "notes": "Leave at door"
}
```

Price is fetched server-side. Do not send `unit_price`.

---

## Environment Variables

```dotenv
# Postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret
USER_DB_NAME=users_db
PRODUCT_DB_NAME=products_db
ORDER_DB_NAME=orders_db

# Service database URLs
USER_DATABASE_URL=postgresql://postgres:secret@postgres_users:5432/users_db
PRODUCT_DATABASE_URL=postgresql://postgres:secret@postgres_products:5432/products_db
ORDER_DATABASE_URL=postgresql://postgres:secret@postgres_orders:5432/orders_db

# RabbitMQ
RABBITMQ_DEFAULT_USER=admin
RABBITMQ_DEFAULT_PASS=secret
RABBITMQ_URL=amqp://admin:secret@rabbitmq:5672/

# Redis
REDIS_URL=redis://redis:6379/0

# Service URLs (internal Docker network)
USER_SERVICE_URL=http://user-service:8000
PRODUCT_SERVICE_URL=http://product-service:8000
ORDER_SERVICE_URL=http://order-service:8000

# Auth
SECRET_KEY=your-django-secret-key
JWT_SECRET=your-jwt-secret-32-chars-minimum
INTERNAL_SECRET=your-internal-secret

# App
DEBUG=True
ALLOWED_HOSTS=*
CORS_ALLOW_ALL=True
SERVICE_REQUEST_TIMEOUT=5
```

---

## Admin Panels

Each service has an independent admin panel:

| Service | URL |
|---|---|
| User Service | http://localhost:8001/admin/ |
| Product Service | http://localhost:8002/admin/ |
| Order Service | http://localhost:8003/admin/ |
| RabbitMQ Management | http://localhost:15672 |

---

## Project Structure

```
bazar/
├── docker-compose.yml
├── nginx/
│   └── nginx.conf
└── services/
    ├── user-service/
    │   └── user_service/
    │       ├── apps/users/
    │       │   ├── models.py       # Custom UUID User model
    │       │   ├── serializers.py  # JWT with embedded claims
    │       │   ├── views.py
    │       │   ├── events.py       # RabbitMQ publisher
    │       │   └── urls.py
    │       └── settings.py
    ├── product-service/
    │   └── product_service/
    │       ├── apps/products/
    │       │   ├── models.py       # Product with UUID created_by
    │       │   ├── views.py        # IsSellerOrReadOnly + IsInternalService
    │       │   ├── permissions.py
    │       │   ├── authentication.py  # FakeUser — no DB auth
    │       │   └── urls.py
    │       └── settings.py
    └── order-service/
        └── order_service/
            ├── apps/orders/
            │   ├── models.py       # Order + OrderItem with select_for_update
            │   ├── serializers.py  # Fetches prices from Product Service
            │   ├── views.py        # Stock reservation logic
            │   ├── permissions.py  # OrderAccessPermission
            │   ├── authentication.py
            │   └── urls.py
            └── settings.py
```

---

## What's Not Yet Implemented

- **Event consumers** — RabbitMQ events are published but not consumed
- **Redis caching** — Redis is connected but unused
- **Stock rollback (Saga pattern)** — if stock reservation fails mid-order, already-reserved stock is not released
- **Asymmetric JWT (RS256)** — all services share one secret; production should use private/public key pairs
- **Centralized logging** — no correlation IDs across services
- **Token blacklisting** — logout does not invalidate tokens
