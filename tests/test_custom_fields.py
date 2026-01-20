#!/usr/bin/env python3
"""
Test script for custom fields feature
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5001"

def test_custom_fields():
    """Test the custom fields feature end-to-end"""
    
    print("Testing Custom Fields Feature")
    print("=" * 50)
    
    # Note: This test requires authentication for admin endpoints
    # For now, we'll just test the public badge creation API
    
    print("\n1. Testing badge creation with custom data via API...")
    
    badge_data = {
        "recipient_name": "Test User",
        "recipient_email": "test@example.com",
        "custom_data": {
            "score": "95",
            "grade": "A+"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/badges",
            json=badge_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            result = response.json()
            print("✓ Badge created successfully!")
            print(f"  Badge UUID: {result['badge']['uuid']}")
            print(f"  Public URL: {result['public_url']}")
            print(f"  Custom Data: {result['badge']['custom_data']}")
            
            # Verify custom data was stored
            if result['badge']['custom_data'] == badge_data['custom_data']:
                print("✓ Custom data stored correctly!")
            else:
                print("✗ Custom data mismatch!")
                
        else:
            print(f"✗ Failed to create badge: {response.status_code}")
            print(f"  Error: {response.text}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("\nManual testing steps:")
    print("1. Open http://127.0.0.1:5001/admin")
    print("2. Login with credentials")
    print("3. Create a custom field (e.g., 'Score')")
    print("4. Edit a template and enable the custom field")
    print("5. Go to home page and create a badge with custom field value")
    print("6. Verify the custom field appears on the badge image")


if __name__ == '__main__':
    test_custom_fields()
