# locotion/urls.py

from django.contrib import admin
from django.urls import path, include # Added include
# Import views directly from the app
from accounts import views as accounts_views
# If using Django's built-in login/logout views:
from django.contrib.auth import views as auth_views
# For serving static files during development
from django.conf import settings
from django.conf.urls.static import static
# Removed duplicate imports

urlpatterns = [
    path('admin/', admin.site.urls),
    # Home page using the view from 'accounts' app
    path('', accounts_views.home, name='home'),

    # --- Authentication URLs ---
    # Use the functional signup view from 'accounts' app
    path('signup/', accounts_views.signup, name='signup'),

    # Use Django's built-in Login view
    # Ensure you have a 'templates/registration/login.html' template
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),

    # Use Django's built-in Logout view
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'), # Redirects to home after logout

    # Add other app URLs if needed, e.g.:
    # path('app_name/', include('app_name.urls')),

    # You can remove the old favicon path if not needed or ensure it works
    # path('favicon.ico', serve, {'path': 'images/favicon.ico'}),
]

# Serve static files during development ONLY
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # If you also have media files:
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)