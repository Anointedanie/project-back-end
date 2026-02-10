# Learning Guide: Django Authentication System

## 📚 For Junior Developers

This guide explains the key concepts and decisions made in building this authentication system.

---

## 🎯 Why We Made These Choices

### 1. **Email-Based Authentication Instead of Username**

**What we did**: Used email as the unique identifier instead of Django's default username.

**Why**:
- **Better UX**: Users remember their email better than random usernames
- **Professional**: Most modern apps use email authentication
- **Future-ready**: Easy to integrate with AWS SES for email verification
- **Unique by nature**: Emails are naturally unique, no username conflicts

**How we did it**:
```python
# In accounts/models.py
USERNAME_FIELD = 'email'  # This tells Django to use email for login
```

### 2. **Custom User Model vs Django's Default**

**What we did**: Created a custom User model by extending `AbstractBaseUser`.

**Why**:
- **Flexibility**: Can add custom fields anytime (e.g., phone_number, address)
- **Best Practice**: Django documentation recommends this for new projects
- **Future-proof**: Changing User model later is extremely difficult
- **Control**: We control exactly what fields exist

**Key Lesson**: ALWAYS use a custom User model in new Django projects, even if you don't need custom fields yet!

---

## 🔐 Understanding JWT Authentication

### What is JWT?

JWT (JSON Web Token) is a secure way to transmit information between parties as a JSON object.

### Traditional Session vs JWT

**Session-based (Old way)**:
```
User logs in → Server creates session → Stores in database
User makes request → Sends session ID → Server checks database
```
❌ Problems:
- Server must store sessions (uses memory/database)
- Harder to scale across multiple servers
- Not great for microservices

**JWT-based (Modern way)**:
```
User logs in → Server creates JWT token → Sends to user
User makes request → Sends JWT token → Server verifies signature
```
✅ Benefits:
- Stateless (server doesn't store anything)
- Easily scalable
- Perfect for microservices
- Works great with mobile apps

### How Our JWT System Works

```
1. User logs in with email/password
   ↓
2. Server validates credentials
   ↓
3. Server generates TWO tokens:
   - Access Token (short-lived: 60 min)
   - Refresh Token (long-lived: 24 hours)
   ↓
4. User stores both tokens (frontend)
   ↓
5. For API requests:
   - Send: Authorization: Bearer <access_token>
   ↓
6. When access token expires:
   - Use refresh token to get new access token
   - No need to login again
   ↓
7. When refresh token expires:
   - User must login again
```

### Why Two Tokens?

**Access Token (Short-lived)**:
- Used for every API request
- If stolen, only valid for 60 minutes
- Limited damage potential

**Refresh Token (Long-lived)**:
- Only used to get new access tokens
- Stored more securely
- Can be blacklisted on logout

---

## 🏗️ Understanding Django Architecture

### MVT Pattern (Model-View-Template)

Django uses MVT, but for APIs, we modify it:

```
Model (M) - Database structure
  ↓
View (V) - Business logic (we call these ViewSets/APIViews)
  ↓
Serializer (S) - Data conversion (replaces Template)
  ↓
JSON Response
```

### Our File Structure Explained

```
accounts/
├── models.py          # Database schema (User table)
├── serializers.py     # Converts data: Python ↔ JSON
├── views.py           # Business logic (what happens when API is called)
├── urls.py            # URL routing (which URL calls which view)
├── admin.py           # Django admin panel configuration
└── apps.py            # App configuration
```

### How a Request Flows Through Django

```
1. Request: POST /api/auth/login/
   ↓
2. urls.py: Routes to UserLoginView
   ↓
3. views.py: UserLoginView.post() executes
   ↓
4. serializers.py: Validates input data
   ↓
5. models.py: Checks User in database
   ↓
6. views.py: Generates JWT tokens
   ↓
7. serializers.py: Formats response data
   ↓
8. Response: JSON with user data + tokens
```

---

## 🛠️ Understanding Each File

### models.py - The Database Blueprint

```python
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)  # VARCHAR(255) UNIQUE in SQL
    first_name = models.CharField(max_length=150)  # VARCHAR(150)
    is_admin = models.BooleanField(default=False)  # BOOLEAN DEFAULT FALSE
```

**What Django does behind the scenes**:
1. Creates a database table named `accounts_user`
2. Generates SQL commands to create the table
3. Handles all database operations

**SQL equivalent**:
```sql
CREATE TABLE accounts_user (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(150),
    is_admin BOOLEAN DEFAULT FALSE,
    password VARCHAR(128) NOT NULL
);
```

### serializers.py - Data Conversion

**Purpose**: Convert between Python objects and JSON

```python
# Python object (from database)
user = User.objects.get(email='john@example.com')

# Serializer converts to JSON
serializer = UserSerializer(user)
serializer.data
# Output: {'id': 1, 'email': 'john@example.com', ...}
```

**Validation**:
```python
class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise ValidationError("Passwords don't match")
        return attrs
```

### views.py - Business Logic

**APIView vs GenericView**:

```python
# APIView - Full control
class UserLoginView(APIView):
    def post(self, request):
        # You write all logic
        pass

# GenericView - Less code, common patterns
class UserRegistrationView(generics.CreateAPIView):
    # Django handles create logic
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
```

**Permission Classes**:
```python
permission_classes = [permissions.AllowAny]  # Anyone can access
permission_classes = [permissions.IsAuthenticated]  # Login required
```

---

## 🗄️ Database Concepts

### Migrations - Version Control for Database

**What are migrations?**
Think of migrations like Git commits, but for your database schema.

```bash
# Create migration (like git add)
python manage.py makemigrations

# Apply migration (like git commit)
python manage.py migrate
```

**Migration file example**:
```python
# accounts/migrations/0001_initial.py
operations = [
    migrations.CreateModel(
        name='User',
        fields=[
            ('id', models.BigAutoField(primary_key=True)),
            ('email', models.EmailField(unique=True)),
        ],
    ),
]
```

### ORM (Object-Relational Mapping)

**Instead of writing SQL**:
```sql
SELECT * FROM accounts_user WHERE email = 'john@example.com';
```

**We write Python**:
```python
User.objects.get(email='john@example.com')
```

**Common ORM Operations**:
```python
# CREATE
user = User.objects.create(email='new@example.com', password='pass')

# READ
users = User.objects.all()  # Get all users
user = User.objects.get(id=1)  # Get specific user
admins = User.objects.filter(is_admin=True)  # Filter users

# UPDATE
user.first_name = 'Updated'
user.save()

# DELETE
user.delete()
```

---

## 🔒 Security Best Practices We Implemented

### 1. Password Hashing

**What we did**:
```python
user.set_password(password)  # Hashes password
user.check_password(password)  # Verifies hashed password
```

**Why**: Passwords are NEVER stored in plain text. We use Django's built-in PBKDF2 algorithm.

**Database storage**:
```
Plain text (❌ NEVER DO THIS): "password123"
Hashed (✅ CORRECT): "pbkdf2_sha256$260000$xyz..."
```

### 2. Token Blacklisting

**What we did**: When user logs out, we blacklist the refresh token.

**Why**: Prevents token reuse if stolen.

```python
# In UserLogoutView
token = RefreshToken(refresh_token)
token.blacklist()  # Token cannot be used again
```

### 3. CORS Configuration

**What we did**:
```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # React frontend
]
```

**Why**: Prevents unauthorized websites from calling our API.

### 4. Password Validation

**What we did**:
```python
validators=[validate_password]  # Django's built-in validators
```

**Checks**:
- Minimum 8 characters
- Not too similar to user info
- Not a common password
- Not entirely numeric

---

## 🎓 Understanding User Roles

### Why We Have Different User Types

```python
class User(AbstractBaseUser):
    is_admin = models.BooleanField(default=False)  # Product management
    is_staff = models.BooleanField(default=False)  # Django admin access
    is_superuser = models.BooleanField(default=False)  # Full control
```

**Use cases**:

1. **Regular User** (`is_admin=False`):
   ```
   Can: Browse products, add to cart, checkout
   Cannot: Manage products, access admin panel
   ```

2. **Product Admin** (`is_admin=True`):
   ```
   Can: Upload products, set prices, manage inventory
   Cannot: Access Django admin, manage users
   ```

3. **Superuser** (`is_superuser=True, is_staff=True`):
   ```
   Can: Everything (development/maintenance)
   ```

### Permission Checks in Views

```python
def get_queryset(self):
    if self.request.user.is_admin or self.request.user.is_staff:
        return User.objects.all()  # Admins see all users
    return User.objects.none()  # Others see nothing
```

---

## 🚀 Development Workflow

### Typical Feature Development

```
1. Plan the feature
   ↓
2. Create/modify models.py
   ↓
3. Create serializers.py
   ↓
4. Create views.py
   ↓
5. Add URL routes in urls.py
   ↓
6. Create migrations
   ↓
7. Apply migrations
   ↓
8. Test in Django admin or API client
   ↓
9. Write tests (we'll add this later)
```

### Testing Your Code

**Manual testing with curl**:
```bash
# Test registration
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123","password2":"test123","first_name":"Test","last_name":"User"}'
```

**Or use our test script**:
```bash
./test_api.sh
```

---

## 📊 Database Migration from SQLite to PostgreSQL

### Current: SQLite
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**Advantages**:
- Zero configuration
- File-based (easy to delete/reset)
- Perfect for development

**Limitations**:
- Not production-ready
- Limited concurrent writes
- No advanced features

### Future: PostgreSQL (AWS RDS)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ecommerce_db',
        'USER': 'postgres',
        'PASSWORD': 'secret',
        'HOST': 'mydb.xyz.rds.amazonaws.com',
        'PORT': '5432',
    }
}
```

**Advantages**:
- Production-ready
- High concurrency
- Advanced features (full-text search, JSON fields)
- Managed backups (AWS RDS)

**Migration steps** (we'll do this later):
1. Set up AWS RDS PostgreSQL instance
2. Update `.env` file with credentials
3. Run migrations: `python manage.py migrate`
4. Import existing data if needed

---

## 🤔 Common Questions

### Q: Why do we need both access and refresh tokens?

**A**: Security + UX balance
- Access token: Short-lived, sent with every request. If stolen, damage is limited.
- Refresh token: Long-lived, only used occasionally. User doesn't need to login frequently.

### Q: What's the difference between `create_user` and `create_superuser`?

**A**:
```python
# Regular user
User.objects.create_user(email='user@example.com', password='pass')
# Sets: is_staff=False, is_superuser=False

# Superuser
User.objects.create_superuser(email='admin@example.com', password='pass')
# Sets: is_staff=True, is_superuser=True
```

### Q: Why use Django REST Framework instead of plain Django?

**A**: DRF provides:
- Built-in API views (less code)
- Serializers (automatic validation)
- Authentication classes (JWT, Token, etc.)
- Browsable API (great for development)
- Throttling, pagination, filtering (out of the box)

### Q: What's the point of `AUTH_USER_MODEL`?

**A**: It tells Django which model to use for authentication. By setting:
```python
AUTH_USER_MODEL = 'accounts.User'
```
We can reference users anywhere:
```python
from django.contrib.auth import get_user_model
User = get_user_model()  # Gets our custom User model
```

---

## 🎯 Next Steps in Your Learning Journey

1. **Understand this authentication system thoroughly**
   - Read each file carefully
   - Understand why each line exists
   - Test the API endpoints

2. **Learn about Products App** (coming next)
   - Models with relationships (ForeignKey)
   - Image uploads
   - Admin-only endpoints

3. **Practice Django ORM**
   - Use Django shell to query database
   - Practice filtering, aggregation
   - Understand query optimization

4. **Study REST API best practices**
   - HTTP methods (GET, POST, PUT, DELETE)
   - Status codes (200, 201, 400, 401, 404)
   - API versioning

---

## 📚 Recommended Resources

1. **Django Official Tutorial**: https://docs.djangoproject.com/en/4.2/intro/tutorial01/
2. **DRF Tutorial**: https://www.django-rest-framework.org/tutorial/1-serialization/
3. **JWT Explained**: https://jwt.io/introduction
4. **SQL for Django Developers**: Practice SQL to understand what ORM does

---

## 💡 Pro Tips

1. **Always activate virtual environment**:
   ```bash
   source venv/bin/activate  # Check prompt changes to (venv)
   ```

2. **Use Django shell for testing**:
   ```bash
   python manage.py shell
   >>> from accounts.models import User
   >>> User.objects.all()
   ```

3. **Check migrations before running**:
   ```bash
   python manage.py showmigrations  # See which are applied
   ```

4. **Use Django admin for quick data checks**:
   - Navigate to http://localhost:8000/admin
   - View/edit data visually

5. **Read error messages carefully**:
   - Django gives excellent error pages in DEBUG mode
   - Stack traces show exact line of error

---

**Remember**: You don't need to understand everything immediately. Focus on:
1. How requests flow through the system
2. What each file does
3. How to test your changes
4. How to debug when things go wrong

Keep building, keep learning! 🚀
