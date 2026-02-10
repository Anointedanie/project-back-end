# System Architecture - E-Commerce Backend

## 🏛️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      React Frontend                         │
│              (http://localhost:3000)                        │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ User Login   │  │ Admin Login  │  │ Product List │    │
│  │ Page         │  │ Page         │  │ Shopping Cart│    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP Requests (JSON)
                            │ Authorization: Bearer <JWT>
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Django REST API                           │
│              (http://localhost:8000)                        │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              CORS Middleware                          │  │
│  │    (Allows requests from React frontend)             │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↓                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         JWT Authentication Middleware                 │  │
│  │    (Verifies access tokens for protected routes)     │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↓                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Accounts    │  │  Products    │  │   Orders     │    │
│  │  App         │  │  App         │  │   App        │    │
│  │              │  │              │  │              │    │
│  │ • Register   │  │ • List       │  │ • Cart       │    │
│  │ • Login      │  │ • Create     │  │ • Checkout   │    │
│  │ • Profile    │  │ • Update     │  │ • History    │    │
│  │ • Logout     │  │ • Delete     │  │              │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ ORM (Django Models)
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Database Layer                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Current: SQLite (Development)                      │   │
│  │  File: db.sqlite3                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Future: PostgreSQL on AWS RDS (Production)         │   │
│  │  Host: xxx.rds.amazonaws.com                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Request Flow Diagram

### User Login Flow

```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. POST /api/auth/login/
     │    {email, password}
     ↓
┌────────────────────┐
│  Django URLs       │
│  config/urls.py    │
└────┬───────────────┘
     │ 2. Route to accounts.urls
     ↓
┌────────────────────┐
│  Accounts URLs     │
│  accounts/urls.py  │
└────┬───────────────┘
     │ 3. Route to UserLoginView
     ↓
┌─────────────────────────┐
│  UserLoginView          │
│  accounts/views.py      │
│                         │
│  • Validate input       │
│  • Authenticate user    │
│  • Generate JWT tokens  │
└────┬────────────────────┘
     │ 4. Query database
     ↓
┌──────────────────┐
│  User Model      │
│  accounts/models │
│  (via ORM)       │
└────┬─────────────┘
     │ 5. Return user data
     ↓
┌─────────────────────────┐
│  JWT Token Generation   │
│  (SimpleJWT library)    │
│                         │
│  • Create access token  │
│  • Create refresh token │
└────┬────────────────────┘
     │ 6. Format response
     ↓
┌──────────────────────┐
│  UserSerializer      │
│  accounts/serializer │
└────┬─────────────────┘
     │ 7. Return JSON
     ↓
┌──────────────────────────────┐
│  Response                    │
│  {                           │
│    user: {...},              │
│    tokens: {                 │
│      access: "...",          │
│      refresh: "..."          │
│    }                         │
│  }                           │
└──────────────────────────────┘
```

---

## 🗄️ Database Schema (Current)

```
┌──────────────────────────────────────────┐
│              accounts_user               │
├──────────────────────────────────────────┤
│ id (PK)              BIGINT AUTO         │
│ email                VARCHAR(255) UNIQUE │
│ password             VARCHAR(128)        │
│ first_name           VARCHAR(150)        │
│ last_name            VARCHAR(150)        │
│ is_admin             BOOLEAN DEFAULT 0   │
│ is_active            BOOLEAN DEFAULT 1   │
│ is_staff             BOOLEAN DEFAULT 0   │
│ is_superuser         BOOLEAN DEFAULT 0   │
│ date_joined          DATETIME            │
│ last_login           DATETIME            │
└──────────────────────────────────────────┘

Future tables (to be implemented):

┌──────────────────────────────────────────┐
│             products_product             │
├──────────────────────────────────────────┤
│ id (PK)              BIGINT AUTO         │
│ name                 VARCHAR(200)        │
│ description          TEXT                │
│ price                DECIMAL(10,2)       │
│ image                VARCHAR(255)        │
│ stock                INTEGER             │
│ created_by (FK)      → accounts_user.id  │
│ created_at           DATETIME            │
│ updated_at           DATETIME            │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│              orders_cart                 │
├──────────────────────────────────────────┤
│ id (PK)              BIGINT AUTO         │
│ user (FK)            → accounts_user.id  │
│ product (FK)         → products_product  │
│ quantity             INTEGER             │
│ created_at           DATETIME            │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│              orders_order                │
├──────────────────────────────────────────┤
│ id (PK)              BIGINT AUTO         │
│ user (FK)            → accounts_user.id  │
│ total_amount         DECIMAL(10,2)       │
│ status               VARCHAR(50)         │
│ created_at           DATETIME            │
└──────────────────────────────────────────┘
```

---

## 🔐 Authentication Flow

```
┌────────────────────────────────────────────────────────┐
│                    Initial Login                       │
└────────────────────────────────────────────────────────┘
                         │
                         ↓
           ┌─────────────────────────┐
           │  User sends credentials │
           │  email + password       │
           └───────────┬─────────────┘
                       │
                       ↓
           ┌─────────────────────────┐
           │  Django authenticates   │
           │  check_password()       │
           └───────────┬─────────────┘
                       │
                       ↓
           ┌─────────────────────────┐
           │  Generate JWT tokens    │
           │  • Access (60 min)      │
           │  • Refresh (24 hours)   │
           └───────────┬─────────────┘
                       │
                       ↓
           ┌─────────────────────────┐
           │  Send tokens to client  │
           │  Store in localStorage  │
           └─────────────────────────┘

┌────────────────────────────────────────────────────────┐
│                 Making API Requests                    │
└────────────────────────────────────────────────────────┘
                         │
                         ↓
           ┌─────────────────────────┐
           │  Include access token   │
           │  Authorization: Bearer  │
           │  <access_token>         │
           └───────────┬─────────────┘
                       │
                       ↓
           ┌─────────────────────────┐
           │  JWT Middleware         │
           │  Verifies signature     │
           │  Checks expiration      │
           └───────────┬─────────────┘
                       │
                   ┌───┴───┐
                   │ Valid?│
                   └───┬───┘
              Yes ─────┤───── No
                  │            │
                  ↓            ↓
         ┌────────────┐  ┌──────────┐
         │ Process    │  │ Return   │
         │ request    │  │ 401 Error│
         └────────────┘  └──────────┘

┌────────────────────────────────────────────────────────┐
│              Token Refresh Flow                        │
└────────────────────────────────────────────────────────┘
                         │
                         ↓
           ┌─────────────────────────┐
           │  Access token expires   │
           │  (after 60 minutes)     │
           └───────────┬─────────────┘
                       │
                       ↓
           ┌─────────────────────────┐
           │  Send refresh token     │
           │  to /token/refresh/     │
           └───────────┬─────────────┘
                       │
                       ↓
           ┌─────────────────────────┐
           │  Verify refresh token   │
           │  Check if blacklisted   │
           └───────────┬─────────────┘
                       │
                       ↓
           ┌─────────────────────────┐
           │  Generate new access    │
           │  token (60 min)         │
           └───────────┬─────────────┘
                       │
                       ↓
           ┌─────────────────────────┐
           │  Return new tokens      │
           │  Continue session       │
           └─────────────────────────┘

┌────────────────────────────────────────────────────────┐
│                    Logout Flow                         │
└────────────────────────────────────────────────────────┘
                         │
                         ↓
           ┌─────────────────────────┐
           │  User clicks logout     │
           └───────────┬─────────────┘
                       │
                       ↓
           ┌─────────────────────────┐
           │  Send refresh token     │
           │  to /logout/            │
           └───────────┬─────────────┘
                       │
                       ↓
           ┌─────────────────────────┐
           │  Blacklist refresh      │
           │  token in database      │
           └───────────┬─────────────┘
                       │
                       ↓
           ┌─────────────────────────┐
           │  Clear tokens from      │
           │  client storage         │
           └───────────┬─────────────┘
                       │
                       ↓
           ┌─────────────────────────┐
           │  User must login again  │
           │  to get new tokens      │
           └─────────────────────────┘
```

---

## 🌐 API Endpoint Structure

```
http://localhost:8000
│
├── /admin/                          (Django Admin Panel)
│
├── /api/
│   │
│   ├── /auth/                       (Accounts App)
│   │   ├── /register/               POST   - Create new user
│   │   ├── /login/                  POST   - Login and get tokens
│   │   ├── /logout/                 POST   - Blacklist refresh token
│   │   ├── /token/refresh/          POST   - Get new access token
│   │   ├── /profile/                GET    - Get user profile
│   │   │                            PUT    - Update user profile
│   │   ├── /change-password/        POST   - Change password
│   │   └── /users/                  GET    - List users (admin only)
│   │
│   ├── /products/                   (Products App - To be implemented)
│   │   ├── /                        GET    - List all products
│   │   │                            POST   - Create product (admin)
│   │   ├── /{id}/                   GET    - Get product details
│   │   │                            PUT    - Update product (admin)
│   │   │                            DELETE - Delete product (admin)
│   │   └── /search/                 GET    - Search products
│   │
│   └── /orders/                     (Orders App - To be implemented)
│       ├── /cart/                   GET    - Get user's cart
│       │                            POST   - Add to cart
│       │                            DELETE - Remove from cart
│       ├── /checkout/               POST   - Create order
│       └── /history/                GET    - Get order history
│
└── /media/                          (Uploaded files - product images)
```

---

## 🔧 Technology Stack Details

### Backend Components

```
┌─────────────────────────────────────────────────────┐
│                  Django 4.2.9                       │
│  • Web framework                                    │
│  • ORM for database operations                      │
│  • User authentication                              │
│  • Admin panel                                      │
└─────────────────────────────────────────────────────┘
                        │
                        ├── Django REST Framework
                        │   • API views and serializers
                        │   • Built-in authentication
                        │   • Browsable API interface
                        │
                        ├── SimpleJWT
                        │   • JWT token generation
                        │   • Token refresh mechanism
                        │   • Token blacklisting
                        │
                        ├── django-cors-headers
                        │   • Cross-Origin Resource Sharing
                        │   • Frontend integration
                        │
                        ├── python-decouple
                        │   • Environment variable management
                        │   • Configuration separation
                        │
                        └── psycopg2-binary
                            • PostgreSQL adapter (for future use)
```

### Database Evolution

```
Development:
┌──────────────────────┐
│      SQLite          │
│  • File-based DB     │
│  • Zero config       │
│  • Easy reset        │
└──────────────────────┘

Production (Future):
┌──────────────────────┐
│  PostgreSQL (RDS)    │
│  • Scalable          │
│  • ACID compliant    │
│  • Managed backups   │
│  • High availability │
└──────────────────────┘
```

---

## 📦 Deployment Architecture (Future)

```
┌───────────────────────────────────────────────────────┐
│                    AWS Cloud                          │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │              Application Load Balancer          │ │
│  │              (SSL Termination)                  │ │
│  └────────────────────┬────────────────────────────┘ │
│                       │                               │
│  ┌────────────────────┴────────────────────────────┐ │
│  │         Kubernetes (EKS) / k3s                  │ │
│  │                                                 │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐    │ │
│  │  │ Frontend │  │ Frontend │  │ Frontend │    │ │
│  │  │  Pod 1   │  │  Pod 2   │  │  Pod 3   │    │ │
│  │  └──────────┘  └──────────┘  └──────────┘    │ │
│  │                                                 │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐    │ │
│  │  │ Backend  │  │ Backend  │  │ Backend  │    │ │
│  │  │  Pod 1   │  │  Pod 2   │  │  Pod 3   │    │ │
│  │  └──────────┘  └──────────┘  └──────────┘    │ │
│  └─────────────────────────────────────────────────┘ │
│                       │                               │
│  ┌────────────────────┴────────────────────────────┐ │
│  │              AWS RDS PostgreSQL                 │ │
│  │              (Multi-AZ Deployment)              │ │
│  └─────────────────────────────────────────────────┘ │
│                       │                               │
│  ┌────────────────────┴────────────────────────────┐ │
│  │              AWS S3                             │ │
│  │              (Product Images)                   │ │
│  └─────────────────────────────────────────────────┘ │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │         CloudWatch (Monitoring & Logs)          │ │
│  └─────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────┘
```

---

## 🐳 Docker Architecture (Future)

```
┌──────────────────────────────────────────────┐
│          docker-compose.yml                  │
└──────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ↓           ↓           ↓
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Frontend │  │ Backend  │  │ Database │
│Container │  │Container │  │Container │
│          │  │          │  │          │
│ React    │  │ Django   │  │PostgreSQL│
│ Nginx    │  │ Gunicorn │  │          │
│          │  │          │  │          │
│ Port:    │  │ Port:    │  │ Port:    │
│ 3000     │  │ 8000     │  │ 5432     │
└──────────┘  └──────────┘  └──────────┘
      │             │             │
      └─────────────┴─────────────┘
               Network: ecommerce_network
```

---

## 📈 Future Enhancements

### Phase 1 (Current) ✅
- User authentication with JWT
- Custom user model
- SQLite database

### Phase 2 (Next)
- Products app with CRUD
- Image upload to local storage
- Admin product management

### Phase 3
- Shopping cart
- Order management
- Checkout flow

### Phase 4
- AWS RDS PostgreSQL integration
- AWS S3 for image storage
- AWS SES for email verification

### Phase 5
- Docker containerization
- k3s deployment
- Monitoring with CloudWatch

### Phase 6
- EKS migration
- Infrastructure as Code (Terraform/Pulumi)
- CI/CD pipeline
- Auto-scaling

---

This architecture is designed to be:
- **Scalable**: Can grow from development to production
- **Maintainable**: Clean separation of concerns
- **Secure**: JWT authentication, password hashing, CORS
- **Cloud-ready**: Easy migration to AWS services
