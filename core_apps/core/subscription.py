from datetime import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from core_apps.account.models import KYC
from core_apps.core.models import SubscriptionPlan, UserSubscription

def subscription_plans(request):
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
    kyc = KYC.objects.get(user=request.user)
    
    # Get user's current subscription if logged in
    current_subscription = None
    if request.user.is_authenticated:
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

@login_required
def create_checkout_session(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
    
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
        return redirect('subscription:plans')

@login_required
def subscription_success(request):
    try:
        subscription = UserSubscription.objects.get(user=request.user)
    except UserSubscription.DoesNotExist:
        subscription = None
    
    context = {
        'subscription': subscription
    }
    return render(request, 'subscription/success.html', context)

@login_required
def cancel_subscription(request):
    if request.method == 'POST':
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            
            # For free plan, just deactivate
            if subscription.plan.plan_type == 'FREE':
                subscription.delete()
            else:
                # For paid plans, cancel in payment processor and update
                subscription.is_active = False
                subscription.canceled_at = timezone.now()
                subscription.save()
            
            messages.success(request, 'Your subscription has been canceled.')
            
        except UserSubscription.DoesNotExist:
            messages.error(request, 'No active subscription found.')
    
    return redirect('subscription:plans')