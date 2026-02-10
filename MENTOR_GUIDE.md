# 👨‍💼 Senior Engineer's Mentoring Guide

## 📋 What We've Built - Phase 1 Complete

Congratulations! We've successfully built the **authentication foundation** for your e-commerce application. Here's what's ready:

### ✅ Completed Components

1. **Custom User Authentication System**
   - Email-based login (no usernames)
   - JWT token authentication (stateless, scalable)
   - Two user types: Regular users and Product admins
   - Password hashing and validation
   - Token refresh mechanism
   - Logout with token blacklisting

2. **Database Schema**
   - Custom User model with proper fields
   - SQLite for development (easy to switch to PostgreSQL later)
   - Migrations system in place

3. **API Endpoints**
   - User registration
   - Login/logout
   - Profile management
   - Password change
   - Token refresh
   - User listing (admin only)

4. **Development Tools**
   - Automated setup script
   - Test user creation command
   - API testing script
   - Comprehensive documentation

---

## 📂 Project Structure Explanation

```
backend/
├── 📘 Documentation Files
│   ├── README.md              # Complete API documentation
│   ├── QUICKSTART.md          # 5-minute setup guide
│   ├── LEARNING_GUIDE.md      # Concepts explained for juniors
│   ├── ARCHITECTURE.md        # System design diagrams
│   └── THIS FILE              # Mentor's guide
│
├── 🔧 Configuration Files
│   ├── manage.py              # Django management command
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example           # Environment variables template
│   ├── .gitignore            # Git ignore rules
│   ├── setup.sh              # Automated setup script
│   └── test_api.sh           # API testing script
│
├── ⚙️ config/                 # Django project settings
│   ├── settings.py           # Main configuration
│   ├── urls.py               # URL routing
│   ├── wsgi.py               # WSGI server config
│   └── asgi.py               # ASGI server config
│
├── 👤 accounts/               # User authentication app
│   ├── models.py             # User model definition
│   ├── serializers.py        # DRF serializers
│   ├── views.py              # API views/endpoints
│   ├── urls.py               # URL routes
│   ├── admin.py              # Django admin config
│   ├── apps.py               # App configuration
│   └── management/           # Custom commands
│       └── commands/
│           └── create_test_users.py
│
├── 📦 products/               # (Placeholder for Phase 2)
│   └── [Basic structure ready]
│
└── 🛒 orders/                 # (Placeholder for Phase 3)
    └── [Basic structure ready]
```

---

## 🎓 Teaching Points for Your Junior Engineer

### Key Concepts They Should Understand

1. **Why Email-Based Authentication?**
   - Talk through the decision: UX, AWS integration readiness
   - Show them the `USERNAME_FIELD = 'email'` in models.py
   - Explain why this is set at the model level

2. **JWT vs Session Authentication**
   - Draw the flow diagrams (see ARCHITECTURE.md)
   - Explain stateless vs stateful
   - Discuss when to use each

3. **Django MVT Pattern**
   - Walk through a request flow from URL to response
   - Show how models, serializers, and views work together
   - Use the LEARNING_GUIDE.md examples

4. **Database Migrations**
   - Explain migrations as "version control for database"
   - Show them how to create and apply migrations
   - Discuss why we never edit migration files directly

5. **Environment Variables**
   - Explain separation of config from code
   - Show them the .env file usage
   - Discuss security implications

---

## 🎯 Next Steps - Your Teaching Roadmap

### Immediate Next Session: Products App

**Learning Objectives**:
- Foreign key relationships
- File uploads (images)
- Permission-based views (admin-only endpoints)
- Advanced querying with Django ORM

**Implementation**:
```python
# products/models.py
class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    stock = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)  # <-- Foreign Key!
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Teaching Points**:
- ForeignKey relationships (one-to-many)
- File upload handling
- Media files configuration
- Admin vs user permissions

### Future Sessions

**Session 3: Shopping Cart & Orders**
- Many-to-many relationships
- Transaction handling
- Order state management

**Session 4: AWS Integration**
- Setting up RDS PostgreSQL
- Database migration from SQLite
- AWS SES for email verification
- S3 for image storage

**Session 5: Dockerization**
- Dockerfile creation
- docker-compose setup
- Multi-container orchestration

**Session 6: Kubernetes Deployment**
- k3s local deployment
- ConfigMaps and Secrets
- Service and Ingress configuration

**Session 7: Production Deployment**
- EKS setup
- CI/CD pipeline
- Infrastructure as Code (Terraform)
- Monitoring and logging

---

## 🎤 How to Conduct Code Reviews

### What to Focus On

1. **Code Understanding**
   ```
   Ask: "Can you explain what this code does?"
   Not: "This code does X"
   ```

2. **Decision Making**
   ```
   Ask: "Why did you choose this approach?"
   Not: "You should have done it this way"
   ```

3. **Problem Solving**
   ```
   Ask: "What other solutions did you consider?"
   Not: "There's a better way"
   ```

### Code Review Checklist

- [ ] Can the junior explain the code flow?
- [ ] Do they understand why each file exists?
- [ ] Can they trace a request from URL to database and back?
- [ ] Do they know when to use different serializers?
- [ ] Can they explain the JWT token flow?
- [ ] Do they understand database migrations?

---

## 🐛 Common Issues & How to Guide Through Them

### Issue 1: "I get errors when running migrations"

**Don't**: Fix it for them
**Do**: Guide them through debugging
```
1. Ask: "What does the error message say?"
2. Ask: "What did you change since it last worked?"
3. Guide: "Let's check the model definition together"
4. Teach: "Migrations errors usually mean model syntax issues"
```

### Issue 2: "The API returns 500 error"

**Don't**: Jump to the code immediately
**Do**: Teach debugging process
```
1. Check Django console for stack trace
2. Read the error message carefully
3. Identify which file and line
4. Understand what the code is trying to do
5. Then fix the issue
```

### Issue 3: "I don't understand serializers"

**Don't**: Explain with more code
**Do**: Use analogies and drawings
```
1. Draw: Data flow (Database → Python → JSON)
2. Explain: Serializers are translators
3. Show: Input data → validation → save → output
4. Practice: Let them write one from scratch
```

---

## 💡 Teaching Best Practices

### 1. Learn by Doing

Instead of: "Here's how authentication works..."
Try: "Let's add a new endpoint together. You type, I'll guide."

### 2. Encourage Questions

Create a safe environment:
- "There are no stupid questions"
- "I had the same question when I started"
- "That's actually a great question because..."

### 3. Use Real-World Examples

Connect concepts to real apps they use:
- "Instagram's login works similarly with JWT"
- "Amazon's product listings use this exact pattern"
- "Your bank app uses refresh tokens for security"

### 4. Celebrate Small Wins

- "Great! You just created your first API endpoint"
- "Nice job tracing through that error"
- "You're thinking like a backend developer now"

### 5. Pair Programming

Do it together:
```
Session 1: You type, they watch and ask questions
Session 2: They type, you guide
Session 3: They code alone, you review
Session 4: They explain to you
```

---

## 📊 Progress Tracking

### Phase 1 (Complete) ✅
- [x] Project structure
- [x] User model
- [x] Authentication endpoints
- [x] JWT integration
- [x] Documentation
- [x] Test users

### Phase 2 (Next)
- [ ] Product model
- [ ] Product CRUD endpoints
- [ ] Image upload
- [ ] Admin permissions
- [ ] Product listing/search

### Phase 3 (Future)
- [ ] Cart functionality
- [ ] Order creation
- [ ] Order history
- [ ] Checkout flow

### Phase 4 (AWS)
- [ ] RDS PostgreSQL
- [ ] S3 for images
- [ ] SES for emails
- [ ] AWS deployment

---

## 🔍 Code Quality Guidelines

Teach them to write:

1. **Clean Code**
   ```python
   # Good
   def create_user(email, password, first_name, last_name):
       """Create a new user account."""
       user = User.objects.create_user(
           email=email,
           password=password,
           first_name=first_name,
           last_name=last_name
       )
       return user
   
   # Bad
   def c(e,p,f,l):
       u=User.objects.create_user(e,p,f,l)
       return u
   ```

2. **Commented Code**
   ```python
   # Good: Explain WHY, not WHAT
   # Using email as USERNAME_FIELD for better UX and AWS SES integration
   USERNAME_FIELD = 'email'
   
   # Bad: Obvious comment
   # Set username field to email
   USERNAME_FIELD = 'email'
   ```

3. **Proper Error Handling**
   ```python
   # Good
   try:
       user = User.objects.get(email=email)
   except User.DoesNotExist:
       return Response({'error': 'User not found'}, status=404)
   
   # Bad
   user = User.objects.get(email=email)  # Crashes if not found!
   ```

---

## 📚 Recommended Learning Path

### Week 1-2: Backend Fundamentals
- ✅ Complete Phase 1 (Authentication)
- Read and understand all documentation
- Practice API calls with curl/Postman
- Explore Django admin panel

### Week 3-4: Products Implementation
- Build Product model together
- Implement CRUD operations
- Handle file uploads
- Add permission checks

### Week 5-6: Frontend Integration
- React basics
- Calling APIs from React
- State management
- Form handling

### Week 7-8: Advanced Features
- Shopping cart logic
- Order management
- Data relationships

### Week 9-10: AWS & Deployment
- AWS RDS setup
- S3 integration
- Docker basics
- k3s deployment

---

## 🎯 Success Metrics

Your junior engineer is ready for the next phase when they can:

- [ ] Explain the entire auth flow without notes
- [ ] Create a new endpoint from scratch
- [ ] Debug common errors independently
- [ ] Understand database relationships
- [ ] Write clean, commented code
- [ ] Use Django shell for testing
- [ ] Read and understand Django errors
- [ ] Explain JWT vs session auth

---

## 🤝 Your Role as a Mentor

### Do:
✅ Ask guiding questions
✅ Encourage experimentation
✅ Share real-world experiences
✅ Celebrate progress
✅ Be patient with mistakes
✅ Provide context for decisions
✅ Code together regularly

### Don't:
❌ Write code for them
❌ Say "just Google it"
❌ Skip explaining the "why"
❌ Rush through concepts
❌ Make them feel bad about mistakes
❌ Assume prior knowledge
❌ Leave them stuck for days

---

## 📞 When to Intervene vs Let Them Struggle

### Let Them Struggle (30 min - 1 hour)
- Syntax errors
- Simple logic bugs
- Missing imports
- Typos in code

### Provide Hints (15-30 min)
- Conceptual misunderstandings
- Wrong approach to problem
- Complex debugging
- Framework-specific issues

### Intervene Immediately
- Stuck for > 2 hours
- Completely wrong direction
- Security vulnerabilities
- Critical production issues

---

## 🎓 Additional Resources for Learning

### For Your Junior:
1. Django Official Docs
2. DRF Tutorial
3. JWT.io for token understanding
4. PostgreSQL Tutorial
5. Docker Getting Started

### For Your Mentoring:
1. "The Pragmatic Programmer"
2. "Clean Code" by Robert Martin
3. "Designing Data-Intensive Applications"
4. AWS Well-Architected Framework

---

## 📝 Session Notes Template

Use this after each session:

```
Date: ___________
Topics Covered:
- 
- 
- 

Challenges Faced:
- 
- 

Progress Made:
- 
- 

Next Session Plan:
- 
- 

Questions to Address:
- 
- 
```

---

## 🎉 Final Notes

You've successfully set up a **production-ready authentication system** that:
- Follows industry best practices
- Is scalable and secure
- Is well-documented
- Is beginner-friendly
- Has a clear path to production

**The foundation is solid. Now it's time to build!**

Next session: Let's implement the Products app together. Come prepared with questions about:
- Database relationships
- File uploads
- Permission systems

---

**Remember**: The goal isn't just to build an app. It's to **build a skilled engineer** who understands the WHY behind every decision.

Good luck with your mentoring! 🚀

---

*This guide was created specifically for training junior engineers on modern backend development practices.*
