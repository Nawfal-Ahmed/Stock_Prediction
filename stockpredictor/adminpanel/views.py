from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import AdminUser
from django.contrib.auth.hashers import make_password 

def admin_signup(request):
    if request.method == "POST":
        full_name = request.POST["full_name"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        if password != confirm_password:
            return render(request, "adminpanel/signup.html", {"error": "Passwords do not match"})

        # Check duplicate email
        if AdminUser.objects.filter(email=email).exists():
            return render(request, "adminpanel/signup.html", {"error": "Email already exists"})

        # Create Admin with hashed password
        admin = AdminUser(
            full_name=full_name,
            email=email,
            password=make_password(password)
        )
        admin.save()

        return redirect("admin_login")  # after signup go to login page

    return render(request, "adminpanel/signup.html")

def admin_login(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user:
            login(request, user)
            return redirect('adminpanel/admin_dashboard')
        else:
            messages.error(request, "Invalid login details")
    return render(request, 'adminpanel/admin_dashboard.html')

def admin_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    return render(request, 'adminpanel/admin_dashboard.html')

def admin_logout(request):
    logout(request)
    return redirect('admin_login')


def user_list(request):
    # You can later add filter, pagination, etc.
    users = AdminUser.objects.all()
    return render(request, "adminpanel/user_list.html", {"users": users})