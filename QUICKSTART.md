# Quick Start Guide - Backend Setup

## 🚀 Get Up and Running in 5 Minutes

This guide will help you set up and test the Django backend quickly.

---

## Prerequisites Check

Before starting, ensure you have:
- ✅ Python 3.9 or higher installed
- ✅ pip (Python package manager)
- ✅ Terminal/Command prompt access

Check your Python version:
```bash
python3 --version
# Should show Python 3.9 or higher
```

---

## Setup (Choose One Method)

### Option A: Automated Setup (Recommended)

```bash
# Navigate to backend directory
cd backend

# Run setup script
chmod +x setup.sh
./setup.sh
```

That's it! The script will:
1. Create virtual environment
2. Install dependencies
3. Create database
4. Create test users

Skip to **Step 4: Start Server** below.

---

### Option B: Manual Setup

**Step 1: Create Virtual Environment**
```bash
cd backend
python3 -m venv venv
```

**Step 2: Activate Virtual Environment**
```bash
# On Mac/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# You should see (venv) in your prompt
```

**Step 3: Install Dependencies**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Step 4: Set Up Environment Variables**
```bash
# Copy example env file
cp .env.example .env

# For now, the defaults work fine. 
# You can edit .env later for customization
```

**Step 5: Create Database**
```bash
# Create migration files
python manage.py makemigrations

# Apply migrations to database
python manage.py migrate
```

**Step 6: Create Test Users**
```bash
python manage.py create_test_users
```

You should see output like:
```
✓ Created superuser: admin@example.com (password: admin123)
✓ Created admin user: productadmin@example.com (password: admin123)
✓ Created regular user: john.doe@example.com (password: user123)
...
```

---

## Step 4: Start the Development Server

```bash
# Make sure virtual environment is active (you should see (venv))
python manage.py runserver
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

**✅ Your backend is now running!**

---

## Step 5: Test the API

### Method A: Using the Test Script

Open a **new terminal** (keep the server running in the first one):

```bash
cd backend
chmod +x test_api.sh
./test_api.sh
```

You should see:
```
✓ Server is running
✓ User registration successful
✓ Login successful
✓ Profile retrieval successful
✓ Token refresh successful
```

### Method B: Manual Testing with curl

**Test 1: Login**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"john.doe@example.com","password":"user123"}'
```

You should get back user data and JWT tokens.

**Test 2: Get Profile** (use the access token from above)
```bash
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

### Method C: Using Django Admin

1. Open browser: http://localhost:8000/admin
2. Login with:
   - Email: `admin@example.com`
   - Password: `admin123`
3. Click on "Users" to see all registered users

---

## 📋 Available Test Accounts

| Email | Password | Type |
|-------|----------|------|
| admin@example.com | admin123 | Superuser (all access) |
| productadmin@example.com | admin123 | Product admin |
| john.doe@example.com | user123 | Regular user |
| jane.smith@example.com | user123 | Regular user |

---

## 📡 Available Endpoints

Base URL: `http://localhost:8000`

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login
- `POST /api/auth/logout/` - Logout
- `POST /api/auth/token/refresh/` - Refresh access token
- `GET /api/auth/profile/` - Get user profile
- `PUT /api/auth/profile/` - Update profile
- `POST /api/auth/change-password/` - Change password

### Admin Panel
- `http://localhost:8000/admin` - Django admin interface

---

## 🐛 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'django'"

**Solution**: Virtual environment not activated or dependencies not installed
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Problem: "django.db.utils.OperationalError: no such table"

**Solution**: Migrations not applied
```bash
python manage.py migrate
```

### Problem: "Port 8000 already in use"

**Solution**: Kill existing process or use different port
```bash
# Use different port
python manage.py runserver 8001

# Or find and kill process using port 8000
# On Mac/Linux:
lsof -ti:8000 | xargs kill -9

# On Windows:
netstat -ano | findstr :8000
taskkill /PID [PID_NUMBER] /F
```

### Problem: Login returns "Invalid email or password"

**Solution**: Make sure you created test users
```bash
python manage.py create_test_users
```

---

## 🎯 Next Steps

Now that your backend is running:

1. **Explore the API**
   - Try different endpoints with curl or Postman
   - Check the Django admin panel

2. **Read the Documentation**
   - `README.md` - Complete API documentation
   - `LEARNING_GUIDE.md` - Understand how everything works
   - `ARCHITECTURE.md` - System design overview

3. **Prepare for Frontend**
   - Note down the API endpoints
   - Understand the request/response format
   - Keep the backend running while developing frontend

4. **Experiment**
   - Create new users via API
   - Try the Django shell: `python manage.py shell`
   - Modify code and see changes (server auto-reloads)

---

## 💡 Useful Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Start server
python manage.py runserver

# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser manually
python manage.py createsuperuser

# Open Django shell
python manage.py shell

# Run tests (when we add them)
python manage.py test

# Deactivate virtual environment
deactivate
```

---

## 📚 Need Help?

1. Check `README.md` for detailed API documentation
2. Read `LEARNING_GUIDE.md` for concept explanations
3. Review `ARCHITECTURE.md` for system design
4. Check Django error pages (very helpful in DEBUG mode)

---

**You're all set! The backend is ready for frontend integration.** 🎉
