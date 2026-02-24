"""Test script to verify the web server works"""
import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test imports
print("Testing imports...")
try:
    from ses_intelligence.web.server import get_application
    print("✅ WSGI application imports successfully")
except Exception as e:
    print(f"❌ WSGI application import failed: {e}")
    sys.exit(1)

try:
    from ses_intelligence.web.views import api_health
    print("✅ Views import successfully")
except Exception as e:
    print(f"❌ Views import failed: {e}")
    sys.exit(1)

try:
    from ses_intelligence.web.settings import ALLOWED_HOSTS
    print(f"✅ Settings import successfully (ALLOWED_HOSTS: {ALLOWED_HOSTS})")
except Exception as e:
    print(f"❌ Settings import failed: {e}")
    sys.exit(1)

# Test Django setup
print("\nTesting Django setup...")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ses_intelligence.web.settings')
try:
    import django
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

# Test URL routing
print("\nTesting URL configuration...")
try:
    from ses_intelligence.web.urls import urlpatterns
    print(f"✅ URL patterns loaded: {len(urlpatterns)} routes")
    for pattern in urlpatterns:
        print(f"   - {pattern.pattern}")
except Exception as e:
    print(f"❌ URL configuration failed: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("✅ All tests passed! Server is ready.")
print("="*50)
