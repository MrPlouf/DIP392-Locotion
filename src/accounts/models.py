from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import os
from django.utils import timezone

def profile_picture_path(instance, filename):
    return f'user_{instance.user.id}/profile_pics/{filename}'

def user_image_path(instance, filename):
    return f'user_{instance.user_profile.user.id}/gallery/{filename}'

def user_document_path(instance, filename):
    year = instance.year or timezone.now().year
    return f'user_{instance.user_profile.user.id}/documents/{year}/{filename}'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to=profile_picture_path, blank=True, null=True)
    language = models.CharField(max_length=50, blank=True, null=True, default="English")
    address = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    document_count = models.IntegerField(default=0) # Updated by signal
    ongoing_status = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Active subscription")
    offer_used = models.CharField(max_length=50, blank=True, null=True, default="Basic")

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def save(self, *args, **kwargs):
        try: # Delete old profile picture if a new one is uploaded
            this = UserProfile.objects.get(id=self.id)
            if this.profile_picture != self.profile_picture and this.profile_picture:
                if os.path.isfile(this.profile_picture.path):
                    os.remove(this.profile_picture.path)
        except UserProfile.DoesNotExist: pass # New object
        except ValueError: pass # profile_picture might be None
        super().save(*args, **kwargs)

class UserImage(models.Model):
    user_profile = models.ForeignKey(UserProfile, related_name='gallery_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=user_image_path)
    caption = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Image for {self.user_profile.user.username} - {self.caption or 'Untitled'}"
    def delete(self, *args, **kwargs):
        if self.image and os.path.isfile(self.image.path): os.remove(self.image.path)
        super().delete(*args, **kwargs)

class Document(models.Model):
    AMOUNT_TYPE_CHOICES = [('EXPENSE', 'Expense'), ('GAIN', 'Gain'), ('INFO', 'Informational')]
    CATEGORY_CHOICES = [('INVOICE', 'Invoice'), ('RECEIPT', 'Receipt'), ('CONTRACT', 'Contract'), ('HOME_PLAN', 'Home Plan'), ('INSURANCE', 'Insurance'), ('BANK_STATEMENT', 'Bank Statement'), ('UTILITY_BILL', 'Utility Bill'), ('OTHER', 'Other')]
    user_profile = models.ForeignKey(UserProfile, related_name='documents', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    document_file = models.FileField(upload_to=user_document_path)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='OTHER')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    year = models.IntegerField(blank=True, null=True, help_text="Year associated with the document")
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    amount_type = models.CharField(max_length=10, choices=AMOUNT_TYPE_CHOICES, default='INFO', blank=True, null=True)
    def __str__(self): return f"{self.title} ({self.user_profile.user.username})"
    def save(self, *args, **kwargs):
        if not self.year and self.uploaded_at: self.year = self.uploaded_at.year
        elif not self.year: self.year = timezone.now().year
        super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        if self.document_file and os.path.isfile(self.document_file.path): os.remove(self.document_file.path)
        super().delete(*args, **kwargs)
    @property
    def file_extension(self): name, extension = os.path.splitext(self.document_file.name); return extension.lower()

class ManualTransaction(models.Model):
    AMOUNT_TYPE_CHOICES = Document.AMOUNT_TYPE_CHOICES
    CATEGORY_CHOICES = [('SALARY', 'Salary'), ('RENT', 'Rent Payment'), ('GROCERIES', 'Groceries'), ('TRANSPORT', 'Transport'), ('ENTERTAINMENT', 'Entertainment'), ('INVESTMENT', 'Investment'), ('OTHER_EXPENSE', 'Other Expense'), ('OTHER_INCOME', 'Other Income')] + Document.CATEGORY_CHOICES
    user_profile = models.ForeignKey(UserProfile, related_name='manual_transactions', on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='OTHER_EXPENSE')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_type = models.CharField(max_length=10, choices=AMOUNT_TYPE_CHOICES)
    def __str__(self): return f"{self.description} ({self.get_amount_type_display()}) - ${self.amount} on {self.date}"
    class Meta: ordering = ['-date']

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created: UserProfile.objects.create(user=instance)
    else: UserProfile.objects.get_or_create(user=instance) # Ensures profile exists for old users

@receiver(post_save, sender=Document)
@receiver(models.signals.post_delete, sender=Document)
def update_profile_document_count(sender, instance, **kwargs):
    profile = instance.user_profile
    if UserProfile.objects.filter(pk=profile.pk).exists(): # Check if profile still exists
        profile.document_count = profile.documents.count()
        profile.save()