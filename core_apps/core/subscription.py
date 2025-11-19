from datetime import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from core_apps.account.models import KYC
from core_apps.core.models import SubscriptionPlan, UserSubscription

def get_user_kyc(user):
    """Helper function to get KYC or return None"""
    try:
        return KYC.objects.get(user=user)
    except KYC.DoesNotExist:
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
@kyc_required
def subscription_plans(request):
    """View to display all subscription plans"""
    try:
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
        kyc = get_user_kyc(request.user)
        
        # Get user's current subscription if logged in
        current_subscription = None
        try:
            current_subscription = UserSubscription.objects.get(user=request.user)
        except UserSubscription.DoesNotExist:
            pass
        
        context = {
            'plans': plans,
            'current_subscription': current_subscription,
            "kyc": kyc,
        }
        return render(request, 'subscription/plans.html', context)
    
    except Exception as e:
        messages.error(request, "An error occurred while loading subscription plans.")
        print(f"Subscription plans error: {e}")
        return redirect("core_apps.account:dashboard")

@login_required
@kyc_required
def create_checkout_session(request, plan_id):
    """Handle subscription checkout and payment processing"""
    try:
        plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
        
        # Check if user already has an active subscription
        try:
            existing_subscription = UserSubscription.objects.get(user=request.user)
            if existing_subscription.is_active:
                messages.info(request, f"You already have an active {existing_subscription.plan.name} subscription.")
                return redirect('subscription:plans')
        except UserSubscription.DoesNotExist:
            pass
        
        # For free plan, just assign it to user
        if plan.plan_type == 'FREE':
            UserSubscription.objects.update_or_create(
                user=request.user,
                defaults={
                    'plan': plan,
                    'is_active': True
                }
            )
            messages.success(request, f'Successfully subscribed to {plan.name} plan!')
            return redirect('subscription:success')
        
        # For paid plans, integrate with Stripe
        # This is where you'd integrate with Stripe, PayPal, etc.
        # For now, we'll simulate a successful payment
        
        try:
            # Simulate payment processing
            # In real implementation, you'd use Stripe Python SDK
            
            UserSubscription.objects.update_or_create(
                user=request.user,
                defaults={
                    'plan': plan,
                    'is_active': True,
                    'current_period_start': timezone.now(),
                    'current_period_end': timezone.now() + timezone.timedelta(days=30)
                }
            )
            
            messages.success(request, f'Successfully subscribed to {plan.name} plan!')
            return redirect('subscription:success')
            
        except Exception as e:
            messages.error(request, 'There was an error processing your payment. Please try again.')
            print(f"Payment processing error: {e}")
            return redirect('subscription:plans')
    
    except SubscriptionPlan.DoesNotExist:
        messages.error(request, "The selected subscription plan was not found.")
        return redirect('subscription:plans')
    
    except Exception as e:
        messages.error(request, "An unexpected error occurred. Please try again.")
        print(f"Checkout session error: {e}")
        return redirect('subscription:plans')

@login_required
@kyc_required
def subscription_success(request):
    """Display subscription success page"""
    try:
        subscription = UserSubscription.objects.get(user=request.user)
        
        context = {
            'subscription': subscription
        }
        return render(request, 'subscription/success.html', context)
    
    except UserSubscription.DoesNotExist:
        messages.error(request, "No subscription found. Please subscribe to a plan first.")
        return redirect('subscription:plans')
    
    except Exception as e:
        messages.error(request, "An error occurred while loading your subscription details.")
        print(f"Subscription success error: {e}")
        return redirect('subscription:plans')

@login_required
@kyc_required
def cancel_subscription(request):
    """Handle subscription cancellation"""
    if request.method == "POST":
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            
            # For free plan, just deactivate
            if subscription.plan.plan_type == 'FREE':
                subscription.delete()
                messages.success(request, 'Your free subscription has been canceled.')
            else:
                # For paid plans, cancel in payment processor and update
                subscription.is_active = False
                subscription.canceled_at = timezone.now()
                subscription.save()
                messages.success(request, 'Your subscription has been canceled.')
            
        except UserSubscription.DoesNotExist:
            messages.error(request, 'No active subscription found.')
        
        except Exception as e:
            messages.error(request, 'An error occurred while canceling your subscription.')
            print(f"Cancel subscription error: {e}")
    
    else:
        messages.warning(request, "Invalid request method.")
    
    return redirect('subscription:plans')

@login_required
@kyc_required
def subscription_details(request):
    """View to display current subscription details"""
    try:
        subscription = UserSubscription.objects.get(user=request.user)
        kyc = get_user_kyc(request.user)
        
        context = {
            'subscription': subscription,
            'kyc': kyc,
        }
        return render(request, 'subscription/details.html', context)
    
    except UserSubscription.DoesNotExist:
        messages.info(request, "You don't have an active subscription.")
        return redirect('subscription:plans')
    
    except Exception as e:
        messages.error(request, "An error occurred while loading subscription details.")
        print(f"Subscription details error: {e}")
        return redirect('subscription:plans')