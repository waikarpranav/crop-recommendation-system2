"""
Quick verification script for JWT authentication implementation.
Run this to verify the authentication system is working.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("[*] Testing imports...")
    try:
        from models import User, Prediction, db
        from auth_utils import (
            hash_password, verify_password,
            generate_token, verify_token,
            token_required
        )
        from schemas import UserRegister, UserLogin, TokenResponse
        print("  [OK] All imports successful")
        return True
    except Exception as e:
        print(f"  [FAIL] Import failed: {e}")
        return False


def test_password_hashing():
    """Test password hashing and verification"""
    print("\n[*] Testing password hashing...")
    try:
        from app import app
        with app.app_context():
            from auth_utils import hash_password, verify_password
            
            password = "TestPassword123"
            hashed = hash_password(password)
            
            assert hashed != password, "Password should be hashed"
            assert verify_password(password, hashed), "Password verification should work"
            assert not verify_password("WrongPassword", hashed), "Wrong password should fail"
            
            print("  [OK] Password hashing works correctly")
            return True
    except Exception as e:
        print(f"  [FAIL] Password hashing failed: {e}")
        return False


def test_token_generation():
    """Test JWT token generation and verification"""
    print("\n[*] Testing JWT token generation...")
    try:
        from app import app
        with app.app_context():
            from auth_utils import generate_token, verify_token
            
            user_id = 1
            email = "test@example.com"
            
            # Generate access token
            token = generate_token(user_id, email)
            assert token is not None, "Token should be generated"
            
            # Verify token
            payload = verify_token(token)
            assert payload is not None, "Token should be valid"
            assert payload['user_id'] == user_id, "User ID should match"
            assert payload['email'] == email, "Email should match"
            assert payload['type'] == 'access', "Token type should be access"
            
            print("  [OK] JWT token generation works correctly")
            return True
    except Exception as e:
        print(f"  [FAIL] Token generation failed: {e}")
        return False


def test_user_model():
    """Test User model methods"""
    print("\n[*] Testing User model...")
    try:
        from app import app, db
        from models import User
        
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Create user
            user = User(
                email='test@example.com',
                username='testuser'
            )
            user.set_password('SecurePass123')
            
            db.session.add(user)
            db.session.commit()
            
            # Test password methods
            assert user.password_hash is not None, "Password should be hashed"
            assert user.check_password('SecurePass123'), "Correct password should verify"
            assert not user.check_password('WrongPassword'), "Wrong password should fail"
            
            # Test to_dict
            user_dict = user.to_dict()
            assert 'email' in user_dict, "Dict should contain email"
            assert 'password_hash' not in user_dict, "Dict should not contain password"
            
            print("  [OK] User model works correctly")
            return True
    except Exception as e:
        print(f"  [FAIL] User model failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pydantic_schemas():
    """Test Pydantic validation schemas"""
    print("\n[*] Testing Pydantic schemas...")
    try:
        from schemas import UserRegister, UserLogin
        from pydantic import ValidationError
        
        # Valid registration
        valid_user = UserRegister(
            email='test@example.com',
            username='testuser',
            password='SecurePass123'
        )
        assert valid_user.email == 'test@example.com'
        
        # Invalid email
        try:
            UserRegister(
                email='not-an-email',
                username='testuser',
                password='SecurePass123'
            )
            assert False, "Should have raised validation error"
        except ValidationError:
            pass  # Expected
        
        # Weak password
        try:
            UserRegister(
                email='test@example.com',
                username='testuser',
                password='weak'
            )
            assert False, "Should have raised validation error"
        except ValidationError:
            pass  # Expected
        
        print("  [OK] Pydantic schemas work correctly")
        return True
    except Exception as e:
        print(f"  [FAIL] Pydantic schemas failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("JWT Authentication Verification")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Password Hashing", test_password_hashing()))
    results.append(("JWT Tokens", test_token_generation()))
    results.append(("User Model", test_user_model()))
    results.append(("Pydantic Schemas", test_pydantic_schemas()))
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{name:.<40} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All verification tests passed! Authentication is working!")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
