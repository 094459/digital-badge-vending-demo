#!/usr/bin/env python3
"""Test script for badge API"""
import requests
import json

BASE_URL = "http://127.0.0.1:5001"

def test_create_badge():
    """Test creating a simple badge"""
    print("Testing badge creation...")
    
    response = requests.post(
        f"{BASE_URL}/api/badges",
        json={
            "recipient_name": "Test User",
            "recipient_email": "test@example.com"
        }
    )
    
    if response.status_code == 201:
        data = response.json()
        print("✓ Badge created successfully!")
        print(f"  UUID: {data['badge']['uuid']}")
        print(f"  Public URL: {data['public_url']}")
        print(f"  QR Code: {data['qr_code_url']}")
        return data['badge']['uuid']
    else:
        print(f"✗ Failed: {response.status_code}")
        print(response.text)
        return None

def test_get_badge(uuid):
    """Test retrieving a badge"""
    print(f"\nTesting badge retrieval for {uuid}...")
    
    response = requests.get(f"{BASE_URL}/api/badges/{uuid}")
    
    if response.status_code == 200:
        data = response.json()
        print("✓ Badge retrieved successfully!")
        print(f"  Name: {data['recipient_name']}")
        print(f"  Created: {data['created_at']}")
    else:
        print(f"✗ Failed: {response.status_code}")

def test_list_templates():
    """Test listing templates"""
    print("\nTesting template listing...")
    
    response = requests.get(f"{BASE_URL}/admin/templates")
    
    if response.status_code == 200:
        templates = response.json()
        print(f"✓ Found {len(templates)} template(s)")
        for template in templates:
            print(f"  - {template['name']} (ID: {template['id']}, Default: {template['is_default']})")
    else:
        print(f"✗ Failed: {response.status_code}")

def test_ai_badge():
    """Test AI badge generation"""
    print("\nTesting AI badge generation...")
    
    response = requests.post(
        f"{BASE_URL}/api/badges",
        json={
            "recipient_name": "AI Test User",
            "use_ai": True,
            "ai_prompt": "A professional achievement badge with blue gradient background and gold star in the center"
        }
    )
    
    if response.status_code == 201:
        data = response.json()
        print("✓ AI badge created successfully!")
        print(f"  UUID: {data['badge']['uuid']}")
        print(f"  Public URL: {data['public_url']}")
    else:
        print(f"✗ Failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("Digital Badge Platform - API Tests")
    print("=" * 50)
    
    # Test basic badge creation
    badge_uuid = test_create_badge()
    
    if badge_uuid:
        # Test badge retrieval
        test_get_badge(badge_uuid)
    
    # Test template listing
    test_list_templates()
    
    # Test AI badge (requires AWS credentials)
    print("\n⚠️  AI badge test requires valid AWS credentials")
    test_ai = input("Run AI badge test? (y/n): ")
    if test_ai.lower() == 'y':
        test_ai_badge()
    
    print("\n" + "=" * 50)
    print("Tests complete!")
