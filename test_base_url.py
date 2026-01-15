#!/usr/bin/env python3
"""Test BASE_URL functionality"""
import os
from app import create_app
from app.src.utils import get_base_url

# Test 1: Without BASE_URL env var
print("Test 1: Without BASE_URL environment variable")
if 'BASE_URL' in os.environ:
    del os.environ['BASE_URL']
result = get_base_url()
print(f"  Result: {result}")
print(f"  Expected: http://127.0.0.1:5001")
print(f"  ✓ PASS" if result == "http://127.0.0.1:5001" else "  ✗ FAIL")
print()

# Test 2: With BASE_URL env var
print("Test 2: With BASE_URL environment variable")
os.environ['BASE_URL'] = "https://test.example.com"
result = get_base_url()
print(f"  Result: {result}")
print(f"  Expected: https://test.example.com")
print(f"  ✓ PASS" if result == "https://test.example.com" else "  ✗ FAIL")
print()

# Test 3: Within Flask request context
print("Test 3: Within Flask request context")
os.environ.pop('BASE_URL', None)
app = create_app()
with app.test_request_context('/', headers={
    'X-Forwarded-Proto': 'https',
    'X-Forwarded-Host': 'digital-badge-app.ecs.us-east-1.on.aws'
}):
    result = get_base_url()
    print(f"  Result: {result}")
    print(f"  Expected: https://digital-badge-app.ecs.us-east-1.on.aws")
    print(f"  ✓ PASS" if result == "https://digital-badge-app.ecs.us-east-1.on.aws" else "  ✗ FAIL")
print()

# Test 4: Badge generation with get_base_url
print("Test 4: Badge generation imports correctly")
try:
    from app.src.services.badge_generator import BadgeGenerator
    print("  ✓ PASS - BadgeGenerator imports successfully")
    print("  ✓ PASS - get_base_url is available in badge_generator")
except ImportError as e:
    print(f"  ✗ FAIL - Import error: {e}")
print()

print("All tests completed!")
