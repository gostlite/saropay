from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from core_apps.userauths.models import User
from core_apps.userauths.forms import UserRegisterForm

def RegisterView(request):
    """Register, validate and redirect new user."""
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            username = form.cleaned_data.get("username")
            messages.success(request, f"Hey {username}, Account created successfully! You'd to submit your KYC.")
            new_user = authenticate(username=form.cleaned_data['email'], password=form.cleaned_data['password1'])
            login(request, new_user)
            return redirect("core_apps.account:account")
        else:
            messages.warning(request, 'Your password must contain 9 or more characters!')
            return redirect("core_apps.userauths:sign-up")
    if request.user.is_authenticated:
        messages.warning(request, f"You're already logged in.")
        return redirect("core_apps.account:account")

    else:
        form = UserRegisterForm()

    context = {
        "form": form
    }
    return render(request, "userauths/sign-up.html", context)

def LoginView(request):
    """Login user"""
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, email=email, password=password)

            if user is not None: # if there is a user
                login(request, user)
                messages.success(request, "You are logged.")
                return redirect("core_apps.account:dashboard")
            else:
                messages.warning(request, "Username or password does not exist")
                return redirect("core_apps.userauths:sign-in")
        except:
            messages.warning(request, "User does not exist")

    if request.user.is_authenticated:
        messages.warning(request, "You are already logged In")
        return redirect("core_app.account:account")
        
    return render(request, "userauths/sign-in.html")

def LogoutView(request):
    """Logout user"""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("core_apps.userauths:sign-in")