from django.urls import path
from core_apps.account import views
from core_apps.core import payment_request


app_name = "core_apps.account"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("", views.account, name="account"),
    path("kyc-reg/", views.kyc_registration, name="kyc-reg"),
    path("payment-request-dashboard/", payment_request.payment_request_dashboard, name="payment-request-dashboard"),
]