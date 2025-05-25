from django.contrib import admin
from django.urls import path
from accounts import views as accounts_views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', accounts_views.home, name='home'),

    path('signup/', accounts_views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name="logout"),

    path('app/overview/', accounts_views.overview_view, name='overview'),
    path('app/documents/', accounts_views.documents_view, name='documents'),
    path('app/documents/<int:doc_id>/delete/', accounts_views.delete_document_view, name='delete_document'),
    path('app/expenses/', accounts_views.expenses_view, name='expenses'),
    path('app/expenses/pdf/', accounts_views.generate_expenses_pdf_view, name='generate_expenses_pdf'),
    path('app/profile/', accounts_views.profile_view, name='profile'),
    path('app/profile/edit/', accounts_views.profile_edit_view, name='profile_edit'),
    path('app/images/add/', accounts_views.add_user_image_view, name='add_user_image'),
    path('app/images/<int:image_id>/delete/', accounts_views.delete_user_image_view, name='delete_user_image'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)