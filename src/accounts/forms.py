from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, UserImage, Document, ManualTransaction
import os
from django.utils import timezone

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True, help_text='Required. Enter a valid email address.')
    class Meta(UserCreationForm.Meta): model = User; fields = ('email',)
    def save(self, commit=True): user = super().save(commit=False); user.username = self.cleaned_data['email']; user.email = self.cleaned_data['email']; user.save() if commit else None; return user
    def clean_email(self): email = self.cleaned_data.get('email'); return forms.ValidationError("An account with this email already exists.") if User.objects.filter(email__iexact=email).exists() else email

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(max_length=254, help_text='Required. Enter a valid email address.')
    class Meta: model = User; fields = ['first_name', 'last_name', 'email']
    def clean_email(self): email = self.cleaned_data.get('email'); return forms.ValidationError("This email address is already in use by another account.") if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists() else email

class UserProfileUpdateForm(forms.ModelForm):
    clear_profile_picture = forms.BooleanField(required=False, label="Remove profile picture")
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'language', 'address', 'country', 'offer_used', 'ongoing_status']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }
    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.cleaned_data.get('clear_profile_picture'):
            if profile.profile_picture and hasattr(profile.profile_picture, 'path') and os.path.isfile(profile.profile_picture.path): # Check path exists
                os.remove(profile.profile_picture.path)
            profile.profile_picture = None
        if commit: profile.save()
        return profile

class UserImageForm(forms.ModelForm):
    class Meta: model = UserImage; fields = ['image', 'caption']; widgets = {'image': forms.ClearableFileInput(attrs={'class': 'form-control-file', 'required': True}), 'caption': forms.TextInput(attrs={'placeholder': 'Optional caption for the image'})}

class DocumentForm(forms.ModelForm):
    year = forms.IntegerField(required=False, initial=lambda: timezone.now().year, widget=forms.NumberInput(attrs={'placeholder': 'e.g., 2023'}))
    class Meta: model = Document; fields = ['title', 'document_file', 'category', 'year', 'description', 'amount', 'amount_type']; widgets = {'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Brief description or notes'}), 'document_file': forms.ClearableFileInput(attrs={'class': 'form-control-file', 'required': True}), 'title': forms.TextInput(attrs={'placeholder': 'e.g., January Electricity Bill'}), 'amount': forms.NumberInput(attrs={'placeholder': 'e.g., 25.99'})}; labels = {'document_file': 'Upload Document', 'amount_type': 'Financial Type'}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'amount' in self.fields: self.fields['amount'].required = False
        if 'amount_type' in self.fields: self.fields['amount_type'].required = False; self.fields['amount_type'].empty_label = "Select Type (Optional)"


class ManualTransactionForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}), initial=timezone.now().date())
    class Meta: model = ManualTransaction; fields = ['date', 'description', 'category', 'amount', 'amount_type']; widgets = {'description': forms.TextInput(attrs={'placeholder': 'e.g., Monthly Salary, Office Supplies'}), 'amount': forms.NumberInput(attrs={'placeholder': 'e.g., 150.75'})}
    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        amount_type = cleaned_data.get("amount_type")
        if amount is not None and amount < 0: self.add_error('amount', "Amount cannot be negative. Use 'Expense' type for negative values.")
        if amount_type not in ['EXPENSE', 'GAIN']: self.add_error('amount_type', "Financial type must be either 'Expense' or 'Gain'.") # Only allow these two for manual
        return cleaned_data