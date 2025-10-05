"""
ASGI config for smartretail project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartretail.settings')

application = get_asgi_application()
