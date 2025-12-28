#!/usr/bin/env python
"""
Script to check the current database state
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Resumatch.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import PasswordResetToken

def check_database():
    """Check the current database state"""
    print("🔍 Checking database state...")
    
    # Check users
    users = User.objects.all()
    print(f"\n👥 Users ({users.count()} total):")
    for user in users:
        print(f"  ID: {user.id}")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  First Name: {user.first_name}")
        print(f"  Last Name: {user.last_name}")
        print(f"  Active: {user.is_active}")
        print(f"  Date Joined: {user.date_joined}")
        print(f"  Password Hash: {user.password[:50]}...")
        print("  " + "-" * 50)
    
    # Check password reset tokens
    tokens = PasswordResetToken.objects.all()
    print(f"\n🔑 Password Reset Tokens ({tokens.count()} total):")
    for token in tokens:
        print(f"  User: {token.user.email}")
        print(f"  Token: {token.token[:20]}...")
        print(f"  Created: {token.created_at}")
        print(f"  Expires: {token.expires_at}")
        print(f"  Used: {token.used}")
        print(f"  Valid: {token.is_valid()}")
        print("  " + "-" * 50)
    
    # Test authentication for specific user
    test_email = "kushalpanthadas44@gmail.com"
    print(f"\n🧪 Testing authentication for: {test_email}")
    
    try:
        user = User.objects.get(email=test_email)
        print(f"  User found: {user.username}")
        print(f"  Can authenticate with username: {user.check_password('testpassword123')}")
        
        # Try to authenticate
        from django.contrib.auth import authenticate
        auth_user = authenticate(username=user.username, password='testpassword123')
        if auth_user:
            print(f"  ✅ Authentication successful with username")
        else:
            print(f"  ❌ Authentication failed with username")
            
        # Try with email
        auth_user = authenticate(username=test_email, password='testpassword123')
        if auth_user:
            print(f"  ✅ Authentication successful with email")
        else:
            print(f"  ❌ Authentication failed with email")
            
    except User.DoesNotExist:
        print(f"  ❌ User not found")

if __name__ == "__main__":
    check_database()

