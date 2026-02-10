# E-Commerce Backend - Django REST API

This is the backend API for the e-commerce application built with Django and Django REST Framework.

## 🏗️ Architecture Overview

### Technology Stack
- **Framework**: Django 4.2.9
- **API**: Django REST Framework
- **Authentication**: JWT (JSON Web Tokens) using SimpleJWT
- **Database**: SQLite (Development) → PostgreSQL (Production/AWS RDS)
- **CORS**: django-cors-headers for frontend integration

### Project Structure
```
backend/
├── config/                 # Project configuration
│   ├── settings.py        # Django settings
│   ├── urls.py            # Main URL routing
│   ├── wsgi.py            # WSGI configuration
│   └── asgi.py            # ASGI configuration
├── accounts/              # User authentication app
│   ├── models.py          # Custom User model
│   ├── serializers.py     # DRF serializers
│   ├── views.py           # API views
│   ├── urls.py            # URL routes
│   ├── admin.py           # Django admin config
│   └── management/        # Custom management commands
├── products/              # Product management (to be implemented)
├── orders/                # Order management (to be implemented)
├── requirements.txt       # Python dependencies
├── manage.py              # Django management script
└── .env                   # Environment variables
```

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Run the setup script** (automated):
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

   Or **manually** follow these steps:

3. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings if needed
   ```

6. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create test users**:
   ```bash
   python manage.py create_test_users
   ```

8. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

The API will be available at: `http://localhost:8000`

## 👤 User Authentication System

### Custom User Model

We've implemented a custom User model with **email as the primary identifier** instead of username. This design provides:

1. **Better user experience**: Users log in with their email
2. **Future AWS Cognito integration**: Easy migration to AWS SES for email verification
3. **Flexibility**: Can add custom fields as needed

#### User Fields:
- `email`: Unique identifier (required)
- `first_name`: User's first name
- `last_name`: User's last name
- `is_admin`: Boolean flag for product administrators
- `is_active`: Account status
- `is_staff`: Django admin panel access
- `password`: Encrypted password
- `date_joined`: Registration timestamp

### User Types

1. **Superuser** (`is_superuser=True, is_staff=True`)
   - Full Django admin access
   - Can manage all users and data
   - Credentials: `admin@example.com / admin123`

2. **Product Admin** (`is_admin=True`)
   - Can upload and manage products
   - Cannot access Django admin panel
   - Credentials: `productadmin@example.com / admin123`

3. **Regular User** (default)
   - Can browse products, add to cart, checkout
   - Credentials: `john.doe@example.com / user123`

## 📡 API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register/` | Register new user | No |
| POST | `/api/auth/login/` | Login and get JWT tokens | No |
| POST | `/api/auth/logout/` | Logout (blacklist refresh token) | Yes |
| POST | `/api/auth/token/refresh/` | Refresh access token | No (needs refresh token) |
| GET | `/api/auth/profile/` | Get current user profile | Yes |
| PUT/PATCH | `/api/auth/profile/` | Update user profile | Yes |
| POST | `/api/auth/change-password/` | Change password | Yes |
| GET | `/api/auth/users/` | List all users (admin only) | Yes (Admin) |

### API Request Examples

#### 1. Register a New User

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "securePass123!",
    "password2": "securePass123!",
    "first_name": "New",
    "last_name": "User",
    "is_admin": false
  }'
```

**Response**:
```json
{
  "user": {
    "id": 1,
    "email": "newuser@example.com",
    "first_name": "New",
    "last_name": "User",
    "full_name": "New User",
    "is_admin": false,
    "is_active": true,
    "date_joined": "2025-01-31T10:30:00Z"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "message": "User registered successfully"
}
```

#### 2. Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "user123"
  }'
```

**Response**:
```json
{
  "user": {
    "id": 3,
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "is_admin": false,
    "is_active": true,
    "date_joined": "2025-01-31T09:00:00Z"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "message": "Login successful"
}
```

#### 3. Get User Profile (Authenticated)

```bash
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 4. Refresh Access Token

```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

#### 5. Logout

```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

## 🔐 JWT Authentication Flow

1. **User logs in** → Receives `access` and `refresh` tokens
2. **Access token** (short-lived: 60 minutes):
   - Used for API requests
   - Include in Authorization header: `Bearer <access_token>`
3. **Refresh token** (long-lived: 24 hours):
   - Used to get new access tokens
   - Stored securely by frontend
4. **When access token expires**:
   - Use refresh token to get new access token
   - No need to re-login
5. **On logout**:
   - Refresh token is blacklisted
   - User must login again

## 🧪 Test Users

The setup script creates these test accounts:

| Email | Password | Role | Access |
|-------|----------|------|--------|
| admin@example.com | admin123 | Superuser | Full system access |
| productadmin@example.com | admin123 | Product Admin | Product management |
| john.doe@example.com | user123 | Regular User | Shopping |
| jane.smith@example.com | user123 | Regular User | Shopping |
| bob.wilson@example.com | user123 | Regular User | Shopping |

## 🔄 Database Migration Path

### Current: SQLite (Development)
- Fast setup, no configuration needed
- Perfect for local development
- File-based database (`db.sqlite3`)

### Next: PostgreSQL on AWS RDS (Production)

When ready to migrate to PostgreSQL:

1. **Update `.env` file**:
   ```env
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=ecommerce_db
   DB_USER=postgres
   DB_PASSWORD=your-password
   DB_HOST=your-rds-endpoint.amazonaws.com
   DB_PORT=5432
   ```

2. **Run migrations**:
   ```bash
   python manage.py migrate
   python manage.py create_test_users
   ```

## 📊 Django Admin Panel

Access the Django admin panel at: `http://localhost:8000/admin`

Login with superuser credentials:
- Email: `admin@example.com`
- Password: `admin123`

From here you can:
- View and manage all users
- View database records
- Manually create/edit/delete data

## 🛠️ Development Tips

### Creating Migrations
Whenever you modify models:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Creating a Superuser Manually
```bash
python manage.py createsuperuser
```

### Running Django Shell
```bash
python manage.py shell
```

Example shell commands:
```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Get all users
users = User.objects.all()

# Get specific user
user = User.objects.get(email='john.doe@example.com')

# Check if user is admin
print(user.is_admin)
```

## 📝 Next Steps

After completing authentication, we'll implement:

1. **Products App**:
   - Product model with fields (name, description, price, image, stock)
   - Product CRUD endpoints
   - Admin-only product management
   - Product listing and search for users

2. **Orders App**:
   - Shopping cart functionality
   - Order creation and management
   - Order history

3. **AWS Integration**:
   - AWS SES for email verification
   - AWS RDS PostgreSQL database
   - AWS S3 for product images

4. **Dockerization**:
   - Dockerfile for Django app
   - Docker Compose for local development

5. **Deployment**:
   - K3s deployment
   - EKS migration
   - CloudFormation/Terraform IaC

## 🐛 Troubleshooting

### Common Issues

**Issue**: "ModuleNotFoundError: No module named 'rest_framework'"
- **Solution**: Make sure virtual environment is activated and dependencies are installed
  ```bash
  source venv/bin/activate
  pip install -r requirements.txt
  ```

**Issue**: "django.db.utils.OperationalError: no such table"
- **Solution**: Run migrations
  ```bash
  python manage.py migrate
  ```

**Issue**: "CORS errors when calling from frontend"
- **Solution**: Make sure your frontend URL is in `CORS_ALLOWED_ORIGINS` in `.env`

## 📚 Learning Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [JWT Authentication](https://django-rest-framework-simplejwt.readthedocs.io/)

---

**Created by**: Senior DevOps Engineer
**For**: Junior Developer Training
**Date**: January 2025
