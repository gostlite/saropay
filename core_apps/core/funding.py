from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist

from core_apps.account.models import KYC
from core_apps.core.models import LoanApplication, GrantApplication, PaymentRequest
from core_apps.core.forms import LoanApplicationForm, GrantApplicationForm

def get_user_kyc(user):
    """Helper function to get KYC or return None"""
    try:
        return KYC.objects.get(user=user)
    except KYC.DoesNotExist:
        return None

def kyc_required(view_func):
    """Decorator to check if user has completed KYC"""
    def wrapper(request, *args, **kwargs):
        kyc = get_user_kyc(request.user)
        if not kyc:
            messages.warning(request, "You need to complete your KYC registration to access this page.")
            return redirect("core_apps.account:kyc-reg")
        return view_func(request, *args, **kwargs)
    return wrapper

def require_completed_payment(view_func):
    """
    Decorator to require completed payment request before accessing view
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "You need to login to access this page.")
            return redirect("core_apps.userauths:sign-in")
        
        # Check KYC first
        kyc = get_user_kyc(request.user)
        if not kyc:
            messages.warning(request, "You need to complete your KYC registration first.")
            return redirect("core_apps.account:kyc-reg")
        
        # Then check payment
        has_completed_payment = PaymentRequest.objects.filter(
            user=request.user, 
            status='completed'
        ).exists()
        
        if not has_completed_payment:
            messages.warning(
                request, 
                'You need to subscribe to a plan to access Grant or Loan applications.Contact Support for more details.'
            )
            return redirect('core_apps.core:subscription-plans')
        
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@kyc_required
def funding_application(request):
    """Main funding application page with both loan and grant forms"""
    try:
        kyc = get_user_kyc(request.user)
        loan_form = LoanApplicationForm()
        grant_form = GrantApplicationForm()
        
        # Set initial values for the current user
        loan_form.fields['email'].initial = request.user.email
        grant_form.fields['email'].initial = request.user.email
        
        context = {
            'loan_form': loan_form,
            'grant_form': grant_form,
            'active_tab': 'loans',
            "kyc": kyc
        }
        return render(request, 'funding/application.html', context)
    
    except Exception as e:
        messages.error(request, "An error occurred while loading the application page.")
        print(f"Funding application error: {e}")
        return redirect("core_apps.account:dashboard")

@login_required
@kyc_required
@require_completed_payment
def submit_loan_application(request):
    """Handle loan application submission"""
    try:
        kyc = get_user_kyc(request.user)
        
        if request.method == 'POST':
            form = LoanApplicationForm(request.POST, request.FILES)
            if form.is_valid():
                loan_application = form.save(commit=False)
                loan_application.user = request.user
                loan_application.save()
                
                messages.success(request, "Loan application submitted successfully!")
                return redirect('core_apps.core:application-submitted', app_type='loan', app_id=loan_application.id)
            else:
                messages.error(request, 'Please correct the errors in the loan application form.')
                print("Loan Form Errors:", form.errors)
        else:
            form = LoanApplicationForm()
            form.fields['email'].initial = request.user.email
        
        context = {
            'loan_form': form,
            'grant_form': GrantApplicationForm(),
            'active_tab': 'loans',
            "kyc": kyc
        }
        return render(request, 'funding/application.html', context)
    
    except Exception as e:
        messages.error(request, "An error occurred while submitting your loan application.")
        print(f"Loan application submission error: {e}")
        return redirect('core_apps.core:funding-application')

@login_required
@kyc_required
@require_completed_payment
def submit_grant_application(request):
    """Handle grant application submission"""
    try:
        kyc = get_user_kyc(request.user)
        
        if request.method == 'POST':
            form = GrantApplicationForm(request.POST, request.FILES)
            if form.is_valid():
                grant_application = form.save(commit=False)
                grant_application.user = request.user
                grant_application.save()
                
                messages.success(request, "Grant application submitted successfully!")
                return redirect('core_apps.core:application-submitted', app_type='grant', app_id=grant_application.id)
            else:
                messages.error(request, 'Please correct the errors in the grant application form.')
                print("Grant Form Errors:", form.errors)
        else:
            form = GrantApplicationForm()
            form.fields['email'].initial = request.user.email
        
        context = {
            'loan_form': LoanApplicationForm(),
            'grant_form': form,
            'active_tab': 'grants',
            "kyc": kyc
        }
        return render(request, 'funding/application.html', context)
    
    except Exception as e:
        messages.error(request, "An error occurred while submitting your grant application.")
        print(f"Grant application submission error: {e}")
        return redirect('core_apps.core:funding-application')

@login_required
@kyc_required
def application_status(request):
    """View to display user's loan and grant application status"""
    try:
        kyc = get_user_kyc(request.user)
        user_loans = LoanApplication.objects.filter(user=request.user).order_by('-application_date')
        user_grants = GrantApplication.objects.filter(user=request.user).order_by('-application_date')
        
        context = {
            'user_loans': user_loans,
            'user_grants': user_grants,
            "kyc": kyc
        }
        return render(request, 'funding/status.html', context)
    
    except Exception as e:
        messages.error(request, "An error occurred while loading your application status.")
        print(f"Application status error: {e}")
        return redirect("core_apps.account:dashboard")

@login_required
def application_submitted(request, app_type, app_id):
    """View to display application submission confirmation"""
    try:
        # Verify the application belongs to the current user
        if app_type == 'loan':
            application = get_object_or_404(LoanApplication, id=app_id, user=request.user)
        elif app_type == 'grant':
            application = get_object_or_404(GrantApplication, id=app_id, user=request.user)
        else:
            messages.error(request, "Invalid application type.")
            return redirect('core_apps.core:funding-application')
        
        kyc = get_user_kyc(request.user)
        
        context = {
            'application': application,
            'app_type': app_type,
            'kyc': kyc,
        }
        return render(request, 'funding/submitted.html', context)
    
    except (LoanApplication.DoesNotExist, GrantApplication.DoesNotExist):
        messages.error(request, "Application not found or you don't have permission to view it.")
        return redirect('core_apps.core:application-status')
    
    except Exception as e:
        messages.error(request, "An error occurred while loading the application details.")
        print(f"Application submitted view error: {e}")
        return redirect('core_apps.core:application-status')

@login_required
@kyc_required
def application_detail(request, app_type, app_id):
    """View to display detailed view of a specific application"""
    try:
        if app_type == 'loan':
            application = get_object_or_404(LoanApplication, id=app_id, user=request.user)
        elif app_type == 'grant':
            application = get_object_or_404(GrantApplication, id=app_id, user=request.user)
        else:
            messages.error(request, "Invalid application type.")
            return redirect('core_apps.core:application-status')
        
        kyc = get_user_kyc(request.user)
        
        context = {
            'application': application,
            'app_type': app_type,
            'kyc': kyc,
        }
        return render(request, 'funding/detail.html', context)
    
    except (LoanApplication.DoesNotExist, GrantApplication.DoesNotExist):
        messages.error(request, "Application not found.")
        return redirect('core_apps.core:application-status')
    
    except Exception as e:
        messages.error(request, "An error occurred while loading the application details.")
        print(f"Application detail error: {e}")
        return redirect('core_apps.core:application-status')