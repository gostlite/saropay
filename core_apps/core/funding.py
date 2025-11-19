from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from core_apps.account.models import KYC
from core_apps.core.models import LoanApplication, GrantApplication, PaymentRequest
from core_apps.core.forms import LoanApplicationForm, GrantApplicationForm


def require_completed_payment(view_func):
    """
    Decorator to require completed payment request before accessing view
    """
    def wrapper(request, *args, **kwargs):
        has_completed_payment = PaymentRequest.objects.filter(
            user=request.user, 
            status='completed'
        ).exists()
        
        if not has_completed_payment:
            messages.warning(
                request, 
                'You need to subscribe to a plan, to access Grant or Loan page.'
            )
            return redirect('core_apps.core:subscription-plans')  # Adjust this URL name as needed
        
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@require_completed_payment
def funding_application(request):
    loan_form = LoanApplicationForm()
    grant_form = GrantApplicationForm()
    
    try:
        kyc = KYC.objects.get(user=request.user)
    except KYC.DoesNotExist:
        kyc = None
        messages.error(request, 'Please complete your KYC verification before applying for funding.')
    
    # Set initial values for the current user
    if request.user.is_authenticated:
        loan_form.fields['email'].initial = request.user.email
        grant_form.fields['email'].initial = request.user.email
    
    context = {
        'loan_form': loan_form,
        'grant_form': grant_form,
        'active_tab': 'loans',
        "kyc": kyc
    }
    return render(request, 'funding/application.html', context)


@login_required
@require_completed_payment
def submit_loan_application(request):
    kyc = KYC.objects.get(user=request.user)

    if request.method == 'POST':
        form = LoanApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            loan_application = form.save(commit=False)
            loan_application.user = request.user
            loan_application.save()
            
            return redirect('core_apps.core:application-submitted', app_type='loan', app_id=loan_application.id)
        else:
            print("Loan Form Errors:", form.errors)
            messages.error(request, f'Please correct the errors below. {form.errors}')
    else:
        form = LoanApplicationForm()
    
    context = {
        'loan_form': form,
        'grant_form': GrantApplicationForm(),
        'active_tab': 'loans',
        "kyc": kyc
    }
    return render(request, 'funding/application.html', context)


@login_required
@require_completed_payment
def submit_grant_application(request):
    try:
        kyc = KYC.objects.get(user=request.user)
    except KYC.DoesNotExist:
        kyc = None
        messages.error(request, 'Please complete KYC verification first.')
    
    if request.method == 'POST':
        form = GrantApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            grant_application = form.save(commit=False)
            grant_application.user = request.user
            grant_application.save()
            
            return redirect('core_apps.core:application-submitted', app_type='grant', app_id=grant_application.id)
        else:
            print("Grant Form Errors:", form.errors)
            messages.error(request, f'Please correct the errors below. {form.errors}')
    else:
        form = GrantApplicationForm()
    
    context = {
        'loan_form': LoanApplicationForm(),
        'grant_form': form,
        'active_tab': 'grants',
        "kyc": kyc
    }
    return render(request, 'funding/application.html', context)


# These views don't need the payment requirement check
@login_required
def application_status(request):
    kyc = KYC.objects.get(user=request.user)
    user_loans = LoanApplication.objects.filter(user=request.user).order_by('-application_date')
    user_grants = GrantApplication.objects.filter(user=request.user).order_by('-application_date')
    
    context = {
        'user_loans': user_loans,
        'user_grants': user_grants,
        "kyc": kyc
    }
    return render(request, 'funding/status.html', context)


@login_required
def application_submitted(request, app_type, app_id):
    if app_type == 'loan':
        application = get_object_or_404(LoanApplication, id=app_id, user=request.user)
    else:
        application = get_object_or_404(GrantApplication, id=app_id, user=request.user)
    
    context = {
        'application': application,
        'app_type': app_type,
    }
    return render(request, 'funding/submitted.html', context)