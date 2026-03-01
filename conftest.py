"""
Pytest configuration for Django tests.

This ensures that:
1. Environment variables are loaded from .env
2. Django is properly configured for testing
3. Test database is used when needed
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env BEFORE Django setup
from dotenv import load_dotenv
load_dotenv()

# Now import Django and configure
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ses_intelligence.web.settings')

import django
django.setup()
