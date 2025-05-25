from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, UserImage, Document, ManualTransaction # Import ManualTransaction

class UserProfileInline(admin.StackedInline): model = UserProfile; can_delete = False; verbose_name_plural = 'User Profile'; fk_name = 'user'; extra = 0
# Removed UserImageInline and DocumentInline from UserAdmin to avoid previous error
# class UserImageInline(admin.TabularInline): model = UserImage; extra = 1
# class DocumentInline(admin.TabularInline): model = Document; extra = 1

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_country_from_profile')
    def get_country_from_profile(self, instance):
        try:
            if hasattr(instance, 'userprofile') and instance.userprofile: return instance.userprofile.country
        except UserProfile.DoesNotExist: pass
        return None
    get_country_from_profile.short_description = 'Country'

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(UserImage)
class UserImageAdmin(admin.ModelAdmin): # Keep as is
    list_display = ('caption', 'user_profile_user', 'image_thumbnail', 'uploaded_at')
    list_filter = ('user_profile__user', 'uploaded_at')
    search_fields = ('caption', 'user_profile__user__username')
    readonly_fields = ('image_thumbnail_display',)
    def user_profile_user(self, obj): return obj.user_profile.user.username
    user_profile_user.short_description = 'User'
    def image_thumbnail(self, obj): from django.utils.html import format_html; return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url) if obj.image else "No Image"
    image_thumbnail.short_description = 'Thumbnail'
    def image_thumbnail_display(self, obj): from django.utils.html import format_html; return format_html('<img src="{}" style="max-height: 200px; max-width: 200px;" />', obj.image.url) if obj.image else "No Image"
    image_thumbnail_display.short_description = 'Image Preview'

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin): # Keep as is
    list_display = ('title', 'user_profile_user', 'category', 'year', 'uploaded_at', 'amount', 'amount_type', 'file_link')
    list_filter = ('category', 'year', 'amount_type', 'user_profile__user')
    search_fields = ('title', 'description', 'user_profile__user__username')
    date_hierarchy = 'uploaded_at'
    def user_profile_user(self, obj): return obj.user_profile.user.username
    user_profile_user.short_description = 'User'
    def file_link(self, obj): from django.utils.html import format_html; return format_html('<a href="{}">View/Download</a>', obj.document_file.url) if obj.document_file else "No File"
    file_link.short_description = 'File'

# --- NEW: REGISTER ManualTransaction ---
@admin.register(ManualTransaction)
class ManualTransactionAdmin(admin.ModelAdmin):
    list_display = ('description', 'user_profile_user', 'date', 'category', 'amount', 'amount_type')
    list_filter = ('date', 'category', 'amount_type', 'user_profile__user')
    search_fields = ('description', 'user_profile__user__username')
    date_hierarchy = 'date'

    def user_profile_user(self, obj):
        return obj.user_profile.user.username
    user_profile_user.short_description = 'User'