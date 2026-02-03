# JWT Authentication System - Quick Start Guide

## 🚀 Installation

### 1. Install New Dependencies

The JWT authentication system requires three new packages:

```bash
cd crop-recommendation-backend
pip install PyJWT==2.8.0 bcrypt==4.1.2 email-validator==2.1.0
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

The server will automatically:
- Create the `users` table
- Add `user_id` column to existing `predictions` table
- Migrate existing data (backward compatible)

---

## 📝 API Usage Examples

### 1. Register a New User

```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "farmer@example.com",
    "username": "farmer123",
    "password": "SecureFarm2024!"
  }'
```

**Response**:
```json
{
  "status": "success",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "farmer@example.com",
    "username": "farmer123",
    "created_at": "2026-02-03T16:30:00",
    "is_active": true
  }
}
```

### 2. Login

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "farmer@example.com",
    "password": "SecureFarm2024!"
  }'
```

### 3. Make a Prediction (Protected)

**Important**: Save the `access_token` from registration/login response!

```bash
curl -X POST http://localhost:5000/api/v1/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -d '{
    "N": 90,
    "P": 42,
    "K": 43,
    "temperature": 20.8,
    "humidity": 82,
    "ph": 6.5,
    "rainfall": 202.9
  }'
```

### 4. Get Your Profile

```bash
curl -X GET http://localhost:5000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

### 5. View Your Prediction History

```bash
curl -X GET http://localhost:5000/api/v1/history?limit=10 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

### 6. Refresh Your Token

When your access token expires (after 1 hour), use the refresh token:

```bash
curl -X POST http://localhost:5000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN_HERE"
  }'
```

---

## 🔒 Security Features

✅ **Bcrypt Password Hashing** - Industry-standard security  
✅ **JWT Tokens** - Stateless authentication  
✅ **Token Expiration** - Access tokens expire after 1 hour  
✅ **Refresh Tokens** - Long-lived tokens for session management  
✅ **Input Validation** - Pydantic schemas with strict validation  
✅ **User Isolation** - Users only see their own predictions  

---

## 📋 Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

Example valid passwords:
- `SecureFarm2024!`
- `MyPassword123`
- `CropRec2024`

---

## 🔑 Protected Endpoints

These endpoints now require authentication (include `Authorization: Bearer <token>` header):

- `POST /api/v1/predict` - Make crop predictions
- `GET /api/v1/history` - View your prediction history
- `GET /api/v1/stats` - View your statistics
- `GET /api/v1/auth/me` - Get your profile

---

## 🌐 Public Endpoints

These endpoints do NOT require authentication:

- `GET /` - API information
- `GET /api/v1/health` - Health check
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token

---

## 🧪 Testing

### Manual Testing

1. **Register a user**:
   ```bash
   curl -X POST http://localhost:5000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@test.com","username":"testuser","password":"TestPass123"}'
   ```

2. **Copy the access_token from the response**

3. **Make a prediction**:
   ```bash
   curl -X POST http://localhost:5000/api/v1/predict \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <YOUR_TOKEN>" \
     -d '{"N":90,"P":42,"K":43,"temperature":20.8,"humidity":82,"ph":6.5,"rainfall":202.9}'
   ```

### Automated Testing

```bash
# Install pytest if not already installed
pip install pytest

# Run all tests
pytest tests/ -v

# Run only authentication tests
pytest tests/test_auth.py -v
```

---

## ⚠️ Common Errors

### 401 Unauthorized
**Cause**: Missing or invalid token  
**Solution**: Include `Authorization: Bearer <token>` header with valid token

### 409 Conflict
**Cause**: Email or username already exists  
**Solution**: Use a different email/username

### 400 Bad Request
**Cause**: Invalid input (weak password, invalid email, etc.)  
**Solution**: Check password requirements and email format

---

## 🔧 Configuration

### Environment Variables

Add to `.env` file:

```bash
# JWT Settings
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=604800

# Database (existing)
DATABASE_URL=your-database-url
```

### Production Deployment

1. Set a strong `JWT_SECRET_KEY`:
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

2. Use HTTPS for all requests

3. Set appropriate CORS settings

4. Enable rate limiting on auth endpoints

---

## 📊 Database Changes

The system automatically creates/updates:

1. **New `users` table**:
   - id, email, username, password_hash
   - created_at, last_login, is_active

2. **Updated `predictions` table**:
   - Added `user_id` foreign key (nullable for backward compatibility)

**Existing predictions** remain accessible with `user_id = NULL`.

---

## 🎯 Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Start the server: `python app.py`
3. Register a user via `/api/v1/auth/register`
4. Use the access token for all predictions
5. Update your frontend to handle authentication

---

## 📚 Documentation

For complete implementation details, see:
- [Implementation Plan](file:///C:/Users/Pranav/.gemini/antigravity/brain/4e216d7e-b53a-4339-ad7f-6f8ac8fd5f99/implementation_plan.md)
- [Walkthrough](file:///C:/Users/Pranav/.gemini/antigravity/brain/4e216d7e-b53a-4339-ad7f-6f8ac8fd5f99/walkthrough.md)
- [Task Checklist](file:///C:/Users/Pranav/.gemini/antigravity/brain/4e216d7e-b53a-4339-ad7f-6f8ac8fd5f99/task.md)

---

**Built with ❤️ for Secure Agriculture** 🌾🔒
