# messaging_app/messaging_app/settings.py

# ... other settings ...

# Add or update the CACHES setting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake', # This can be any unique string
        # 'TIMEOUT': 300, # Optional: default timeout for cache entries (seconds)
    }
}

# ... other settings ...