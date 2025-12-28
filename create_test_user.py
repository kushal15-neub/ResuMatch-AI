#!/usr/bin/env python
"""
Script to create a test user for password reset testing
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

def create_test_user():
    """Create a test user for password reset testing"""
    email = "kushalpanthadas44@gmail.com"
    username = "kushalpanthadas44"
    
    # Check if user already exists
    if User.objects.filter(email=email).exists():
        user = User.objects.get(email=email)
        print(f"User already exists: {user.username} ({user.email})")
        print(f"User ID: {user.id}, Active: {user.is_active}")
        return user
    
    # Create new user
    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password='testpassword123',
            first_name='Kushal',
            last_name='Panthadas'
        )
        print(f"✅ Test user created successfully!")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"User ID: {user.id}")
        print(f"Active: {user.is_active}")
        return user
        
    except Exception as e:
        print(f"❌ Failed to create user: {str(e)}")
        return None

def list_all_users():
    """List all users in the database"""
    users = User.objects.all()
    print(f"\n📋 All users in database ({users.count()} total):")
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Active: {user.is_active}")

if __name__ == "__main__":
    print("Creating test user for password reset testing...")
    user = create_test_user()
    list_all_users()

