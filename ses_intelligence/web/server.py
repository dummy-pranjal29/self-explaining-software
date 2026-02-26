"""
SES Intelligence Embedded Web Server

This module provides the ability to run Django's development server
programmatically without requiring an external Django project.
"""

import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load .env file if it exists
def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
            logger.info(f"Loaded environment from {env_path}")
        except ImportError:
            # Fallback: manual parsing
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip())

# Load .env on module import
load_env_file()


def run_server(host: str = "0.0.0.0", port: int = 8000, open_browser: bool = True):
    """
    Run the embedded SES Intelligence web server.
    
    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to bind to (default: 8000)
        open_browser: Whether to open browser automatically (default: True)
    """
    import django
    from django.conf import settings
    from django.core.management import execute_from_command_line
    
    # Configure Django settings programmatically
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ses_intelligence.web.settings')
    
    # Setup Django
    django.setup()
    
    logger.info(f"Starting SES Intelligence Dashboard on http://{host}:{port}")
    logger.info("Press Ctrl+C to stop the server")
    
    # Open browser if requested
    if open_browser:
        import threading
        import webbrowser
        
        def open_browserDelayed():
            import time
            time.sleep(1.5)  # Wait for server to start
            webbrowser.open(f"http://localhost:{port}")
        
        browser_thread = threading.Thread(target=open_browserDelayed)
        browser_thread.daemon = True
        browser_thread.start()
    
    # Run the development server
    argv = ['manage.py', 'runserver', f'{host}:{port}', '--noreload']
    execute_from_command_line(argv)


def get_application():
    """
    Get the WSGI application for use with production servers (gunicorn, etc.)
    
    Returns:
        WSGI application callable
    """
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ses_intelligence.web.settings')
    django.setup()
    
    from django.core.wsgi import get_wsgi_application
    return get_wsgi_application()


if __name__ == "__main__":
    run_server()
