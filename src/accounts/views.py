from django.shortcuts import render

def home(request):
    context = {
        'title': 'Home Page',
        'welcome': 'Welcome to My WebApp!'
    }
    return render(request, 'home.html', context)

def about(request):
    return render(request, 'about.html', {'title': 'About Us'})