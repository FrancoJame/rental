#!/usr/bin/env python
"""
Script to register a test landlord account
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housing_project.settings')
django.setup()

from django.test import Client
from listings.models import User, LandlordProfile
from listings.forms import LandlordRegisterForm

# Test registration data
registration_data = {
    'username': 'devjohn2026',
    'first_name': 'John',
    'last_name': 'Developer',
    'email': 'devjohn@example.com',
    'phone_number': '0770123456',
    'password': 'TestPassword123!',
    'confirm_password': 'TestPassword123!',
    'national_id_number': '9876543210123',
}

print("🏠 Attempting to register landlord...")
print(f"Username: {registration_data['username']}")
print(f"Email: {registration_data['email']}")
print(f"National ID: {registration_data['national_id_number']}")
print("-" * 50)

# First, validate the form
form = LandlordRegisterForm(registration_data)
if form.is_valid():
    print("✅ Form validation passed!")
    
    # Create a test client
    client = Client()
    
    # Submit the registration form
    response = client.post('/register/', registration_data)
    print(f"\nResponse Status Code: {response.status_code}")
    
    # Check if user was created
    try:
        user = User.objects.get(username=registration_data['username'])
        print(f"✅ User created successfully!")
        print(f"   - Username: {user.username}")
        print(f"   - Email: {user.email}")
        print(f"   - Role: {user.get_role_display()}")
        print(f"   - Is Landlord: {user.role == User.LANDLORD}")
        
        # Check landlord profile
        try:
            profile = LandlordProfile.objects.get(user=user)
            print(f"   - National ID: {profile.national_id_number}")
            print(f"   - Email Verified: {profile.email_verified}")
            print(f"\n✅ Landlord profile created successfully!")
        except LandlordProfile.DoesNotExist:
            print("❌ Landlord profile not found!")
            
    except User.DoesNotExist:
        print("❌ User was not created!")
        
else:
    print("❌ Form validation failed!")
    print("\nForm Errors:")
    for field, errors in form.errors.items():
        print(f"  {field}: {', '.join(errors)}")

print("-" * 50)
print("\n🎉 Registration test completed!")
