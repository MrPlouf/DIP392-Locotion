from django.contrib import admin
from django.urls import path
from accounts.views import home, about  # We'll create these views next
from django.contrib.staticfiles.views import serve
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('about/', about, name='about'),
    path('favicon.ico', serve, {'path': 'images/favicon.ico'}),

]

if settings.DEBUG:  # Only serve static files in development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)