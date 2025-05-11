# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login # Optional: Log in user immediately after signup
from .forms import SignUpForm

def home(request):
    """Renders the home page."""
    return render(request, 'home.html')

# Renamed signup_view to signup and removed the old basic signup view
def signup(request):
    """Handles user signup requests."""
    if request.user.is_authenticated:
        # Optional: Redirect logged-in users away from signup
        return redirect('home') # Or wherever appropriate

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! You are now logged in.')
            # Optional: Log the user in directly after successful signup
            login(request, user)
            # Redirect to a 'success' page or user dashboard (create this later)
            # For now, redirecting home
            return redirect('home')
        else:
            # Form has errors, they will be displayed in the template
            messages.error(request, 'Please correct the errors below.')
    else: # GET request
        form = SignUpForm()

    context = {
        'form': form,
        # 'active_tab': 'signup' # Keep if your simplified template still uses this
    }
    return render(request, 'signup.html', context)

# Add other views for your application here later (e.g., user profile)