import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.inventory.models import Unit
print("Django setup successful")

try:
    count = Unit.objects.count()
    print(f"Database connection successful. Unit count: {count}")
except Exception as e:
    print(f"Database connection failed: {e}")
