# Django-Chat/messaging/urls.py (or your app's urls.py)
from django.urls import path
from django.contrib.auth import views as auth_views # For login/logout
from . import views # Import your app's views

urlpatterns = [
    # ... your other app URLs ...
    path('account/delete/', views.delete_user_account, name='delete_account'),

    # Example: Add login/logout/home if not already present in project urls
    # If these are in your project's main urls.py, you might not need them here.
    # path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    # path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    # path('', some_view_for_home, name='home'), # Define a home view
]

# Ensure your project's main urls.py includes these app URLs, e.g.:
# path('messaging/', include('messaging.urls')),
# And that you have templates for login/logout if using them.
# The 'home' URL name is used in redirects, ensure it's defined.
# If you don't have a 'home', you might redirect to 'login' after account deletion.
# e.g., in views.py: return redirect(reverse('login'))