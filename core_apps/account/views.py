from django.shortcuts import render, redirect
from core_apps.account.models import KYC, Account, Debt, DebtPayment
from core_apps.account.forms import KYCForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core_apps.core.forms import CreditCardForm
from core_apps.core.models import CreditCard
from django.core.exceptions import ObjectDoesNotExist

def get_user_kyc(user):
    """Helper function to get KYC or return None"""
    try:
        return KYC.objects.get(user=user)
    except KYC.DoesNotExist:
        return None

def get_user_account(user):
    """Helper function to get user account"""
    try:
        return Account.objects.get(user=user)
    except Account.DoesNotExist:
        return None

def kyc_required(view_func):
    """Decorator to check if user has completed KYC"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "You need to login to access this page.")
            return redirect("core_apps.userauths:sign-in")
        
        kyc = get_user_kyc(request.user)
        if not kyc:
            messages.warning(request, "You need to complete your KYC registration to access this page.")
            return redirect("core_apps.account:kyc-reg")
        
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
def account(request):
    kyc = get_user_kyc(request.user)
    account = get_user_account(request.user)
    
    if not kyc:
        messages.warning(request, "You need to submit your KYC.")
        return redirect("core_apps.account:kyc-reg")
    
    if not account:
        messages.error(request, "Account not found. Please contact support.")
        return redirect("core_apps.userauths:sign-in")
    
    context = {
        "kyc": kyc,
        "account": account,
    }
    return render(request, "account/account.html", context)

@login_required
def kyc_registration(request):
    account = get_user_account(request.user)
    
    if not account:
        messages.error(request, "Account not found. Please contact support.")
        return redirect("core_apps.userauths:sign-in")
    
    kyc = get_user_kyc(request.user)
    
    if request.method == "POST":
        form = KYCForm(request.POST, request.FILES, instance=kyc)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.user = request.user
            new_form.account = account
            new_form.save()
            messages.success(request, "KYC Form submitted successfully, In review now.")
            return redirect("core_apps.account:account")
    else:
        form = KYCForm(instance=kyc)
    
    context = {
        "account": account,
        "form": form,
        "kyc": kyc,
    }
    return render(request, "account/kyc-form.html", context)

@kyc_required
def dashboard(request):
    account = get_user_account(request.user)
    kyc = get_user_kyc(request.user)
    
    if not account:
        messages.error(request, "Account not found. Please contact support.")
        return redirect("core_apps.userauths:sign-in")
    
    credit_card = CreditCard.objects.filter(user=request.user).order_by("-id")
    
    # Get debt information
    try:
        debt = Debt.objects.get(account=account)
        debt_payments = DebtPayment.objects.filter(debt=debt).order_by("-created_at")[:5]
    except Debt.DoesNotExist:
        debt = None
        debt_payments = None

    if request.method == "POST":
        form = CreditCardForm(request.POST)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.user = request.user
            new_form.save()
            messages.success(request, "Card Added Successfully.")
            return redirect("core_apps.account:dashboard")
    else:
        form = CreditCardForm()
    
    context = {
        "kyc": kyc,
        "account": account,
        "form": form,
        "credit_card": credit_card,
        "debt": debt,
        "debt_payments": debt_payments,
    }
    return render(request, "account/dashboard.html", context)