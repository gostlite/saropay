from django.urls import path
from core_apps.userauths import views


app_name = "core_apps.userauths"

urlpatterns = [
    path("sign-up/", views.RegisterView, name="sign-up"),
    path("sign-in/", views.LoginView, name="sign-in"),
    path("sign-out/", views.LogoutView, name="sign-out"),
]