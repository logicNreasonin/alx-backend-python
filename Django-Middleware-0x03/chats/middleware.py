# Django-Middleware-0x03/chats/middleware.py

import logging
from datetime import datetime, time, timedelta
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from collections import defaultdict
from django.urls import resolve # To identify view/app names if needed

# --- RequestLoggingMiddleware (from previous task) ---
class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('RequestLogger')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler('requests.log')
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def __call__(self, request):
        user_display = str(request.user) if request.user else "Anonymous"
        if hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
            user_display = request.user.username
        log_message = f"{datetime.now()} - User: {user_display} - Path: {request.path}"
        self.logger.info(log_message)
        response = self.get_response(request)
        return response

# --- RestrictAccessByTimeMiddleware (from previous task) ---
class RestrictAccessByTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.start_allowed_hour = 18
        self.end_allowed_hour = 21

    def __call__(self, request):
        if request.path.startswith('/api/conversations/') or \
           request.path.startswith('/api/messages/'):
            current_time = datetime.now().time()
            current_hour = current_time.hour
            if not (self.start_allowed_hour <= current_hour < self.end_allowed_hour):
                return JsonResponse(
                    {"error": "Access to the chat service is restricted at this time. "
                              f"Available between {self.start_allowed_hour}:00 and {self.end_allowed_hour-1}:59."},
                    status=403
                )
        response = self.get_response(request)
        return response

# --- RateLimitMessagesMiddleware (from previous task) ---
class RateLimitMessagesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.requests_log = defaultdict(list)
        self.limit = 5
        self.window = timedelta(minutes=1)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def __call__(self, request):
        if request.method == 'POST' and request.path.startswith('/api/messages/'):
            ip_address = self.get_client_ip(request)
            current_time = datetime.now()
            valid_timestamps = [
                ts for ts in self.requests_log[ip_address]
                if current_time - ts < self.window
            ]
            self.requests_log[ip_address] = valid_timestamps
            if len(self.requests_log[ip_address]) >= self.limit:
                time_to_wait = (self.requests_log[ip_address][0] + self.window) - current_time
                wait_seconds = max(0, time_to_wait.total_seconds())
                return JsonResponse(
                    {"error": f"Rate limit exceeded. You have sent too many messages. "
                              f"Please try again in {int(wait_seconds) + 1} seconds."},
                    status=429
                )
            self.requests_log[ip_address].append(current_time)
        response = self.get_response(request)
        return response

# --- New: RolePermissionMiddleware ---
class RolePermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Define paths that require admin/moderator roles
        # This is a simple example. For complex scenarios, you might use settings
        # or a more sophisticated configuration.
        self.restricted_paths_prefixes = {
            # Example: Let's say managing (DELETE, PUT, PATCH) conversations or messages requires admin/moderator
            # We'll check for methods within these paths in __call__
            '/api/conversations/': ['DELETE', 'PUT', 'PATCH'], # Only these methods are restricted
            '/api/messages/': ['DELETE', 'PUT', 'PATCH'],     # Only these methods are restricted
            # Add more paths and methods as needed
            # e.g., '/admin-only-api/': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
        }

    def __call__(self, request):
        # Ensure user is authenticated before checking roles
        if not request.user.is_authenticated:
            # Let other middleware or views handle unauthenticated users if necessary,
            # or return 401 here if this middleware should always run after auth.
            # Assuming AuthenticationMiddleware has already run and set request.user.
            return self.get_response(request) 

        is_admin = request.user.is_superuser
        is_moderator = request.user.is_staff # Using is_staff as a proxy for moderator

        # Check if the current path and method combination is restricted
        for path_prefix, restricted_methods in self.restricted_paths_prefixes.items():
            if request.path.startswith(path_prefix) and request.method in restricted_methods:
                # Path and method match a restricted rule
                if not (is_admin or is_moderator):
                    return JsonResponse(
                        {"error": "You do not have permission to perform this action. "
                                  "Admin or Moderator role required."},
                        status=403  # Forbidden
                    )
                # If user is admin or moderator, they can proceed for this rule,
                # but we should continue checking other rules if any.
                # For this simple prefix matching, the first match is usually sufficient.
                # If one rule allows, they pass this middleware for this request.
                # To be very strict, if ANY rule restricts and they don't have permission, block.
                # Current logic: if they pass one restriction rule (e.g. path match + role OK), they go on.
                # Let's refine: if the path matches and method matches, AND they are NOT admin/mod, then block.
                break # Found a matching rule, decision made based on this rule for this path.

        return self.get_response(request)