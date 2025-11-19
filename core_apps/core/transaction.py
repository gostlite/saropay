from django.shortcuts import render, get_object_or_404, redirect
from core_apps.core.models import Transaction
from core_apps.account.models import KYC
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist

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

@kyc_required
def transaction_lists(request):
    """View to display all transactions for the user"""
    try:
        # Get transactions
        sender_transaction = Transaction.objects.filter(
            sender=request.user, 
            transaction_type="transfer"
        ).order_by("-id")
        
        receiver_transaction = Transaction.objects.filter(
            receiver=request.user, 
            transaction_type="transfer"
        ).order_by("-id")

        request_sender_transaction = Transaction.objects.filter(
            sender=request.user, 
            transaction_type="request"
        )
        
        request_receiver_transaction = Transaction.objects.filter(
            receiver=request.user, 
            transaction_type="request"
        )

        kyc = get_user_kyc(request.user)
        
        context = {
            "sender_transaction": sender_transaction,
            "receiver_transaction": receiver_transaction,
            "request_sender_transaction": request_sender_transaction,
            "request_receiver_transaction": request_receiver_transaction,  # Fixed typo
            "kyc": kyc,
        }

        return render(request, "transaction/transaction-list.html", context)
    
    except Exception as e:
        messages.error(request, "An error occurred while loading transactions.")
        # Log the actual error for debugging
        print(f"Transaction list error: {e}")
        return redirect("core_apps.account:dashboard")

@kyc_required
def transaction_detail(request, transaction_id):
    """View to display transaction details"""
    try:
        transaction = get_object_or_404(Transaction, transaction_id=transaction_id)
        kyc = get_user_kyc(request.user)
        
        # Check if user is authorized to view this transaction
        if transaction.sender != request.user and transaction.receiver != request.user:
            messages.error(request, "You are not authorized to view this transaction.")
            return redirect("core_apps.account:transaction-lists")
        
        context = {
            "transaction": transaction,
            "kyc": kyc,
        }

        return render(request, "transaction/transaction-detail.html", context)
    
    except Transaction.DoesNotExist:
        messages.error(request, "Transaction not found.")
        return redirect("core_apps.account:transaction-lists")
    
    except Exception as e:
        messages.error(request, "An error occurred while loading transaction details.")
        print(f"Transaction detail error: {e}")
        return redirect("core_apps.account:transaction-lists")