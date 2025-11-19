from django.shortcuts import render, redirect, get_object_or_404
from core_apps.account.models import Account, KYC
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from core_apps.core.forms import PaymentRequestForm
from core_apps.core.models import PaymentRequest, Transaction
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
@kyc_required
def SearchUsersRequest(request):
    """Search user by account number or id"""
    try:
        kyc = get_user_kyc(request.user)
        accounts = Account.objects.all()
        query = request.POST.get("account_number", "").strip()

        if query:
            accounts = accounts.filter(
                Q(account_number=query) |
                Q(account_id=query)
            ).distinct()
        
        context = {
            "accounts": accounts,  # Changed to plural for clarity
            "query": query,
            "kyc": kyc,
        }
        return render(request, "payment_request/search-users.html", context)
    
    except Exception as e:
        messages.error(request, "An error occurred while searching for users.")
        print(f"Search users error: {e}")
        return redirect("core_apps.account:dashboard")

@login_required
@kyc_required
def AmountRequest(request, account_number):
    """Display amount request page for a specific account"""
    try:
        kyc = get_user_kyc(request.user)
        account = get_object_or_404(Account, account_number=account_number)
        
        # Prevent self-request
        if account.user == request.user:
            messages.warning(request, "You cannot request money from your own account.")
            return redirect("core_apps.core:search-users-request")

        context = {
            "account": account,
            "kyc": kyc,
        }
        return render(request, "payment_request/amount-request.html", context)
    
    except Account.DoesNotExist:
        messages.warning(request, "Account does not exist.")
        return redirect("core_apps.core:search-users-request")
    
    except Exception as e:
        messages.error(request, "An error occurred while loading the request page.")
        print(f"Amount request error: {e}")
        return redirect("core_apps.core:search-users-request")

@login_required
@kyc_required
def AmountRequestProcess(request, account_number):
    """Process the amount request"""
    try:
        account = get_object_or_404(Account, account_number=account_number)
        
        # Prevent self-request
        if account.user == request.user:
            messages.warning(request, "You cannot request money from your own account.")
            return redirect("core_apps.core:search-users-request")

        sender = request.user
        receiver = account.user
        sender_account = request.user.account
        receiver_account = account

        if request.method == "POST":
            amount_str = request.POST.get("amount-request", "").strip()
            description = request.POST.get("description", "").strip()

            # Validate amount
            if not amount_str:
                messages.warning(request, "Please enter an amount.")
                return redirect("core_apps.core:amount-request", account_number)
            
            try:
                amount = Decimal(amount_str)
                if amount <= 0:
                    messages.warning(request, "Amount must be greater than zero.")
                    return redirect("core_apps.core:amount-request", account_number)
            except (InvalidOperation, ValueError):
                messages.warning(request, "Invalid amount format.")
                return redirect("core_apps.core:amount-request", account_number)

            # Create payment request transaction
            new_request = Transaction.objects.create(
                user=request.user,
                amount=amount,
                description=description,
                sender=sender,
                receiver=receiver,
                sender_account=sender_account,
                receiver_account=receiver_account,
                status="request_processing",
                transaction_type="request",
            )
            
            transaction_id = new_request.transaction_id
            return redirect("core_apps.core:amount-request-confirmation", account.account_number, transaction_id)
        else:
            messages.warning(request, "Invalid request method.")
            return redirect("core_apps.core:amount-request", account_number)
    
    except Account.DoesNotExist:
        messages.warning(request, "Account does not exist.")
        return redirect("core_apps.core:search-users-request")
    
    except Exception as e:
        messages.error(request, "An error occurred while processing your request.")
        print(f"Amount request process error: {e}")
        return redirect("core_apps.core:amount-request", account_number)

@login_required
@kyc_required
def AmountRequestConfirmation(request, account_number, transaction_id):
    """Display request confirmation page"""
    try:
        account = get_object_or_404(Account, account_number=account_number)
        transaction = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)
        
        # Verify transaction belongs to current user
        if transaction.receiver_account != account:
            messages.warning(request, "Invalid transaction.")
            return redirect("core_apps.account:dashboard")

        kyc = get_user_kyc(request.user)
        
        context = {
            "account": account,
            "transaction": transaction,
            "kyc": kyc,
        }
        return render(request, "payment_request/amount-request-confirmation.html", context)
    
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction or account not found.")
        return redirect("core_apps.account:dashboard")
    
    except Exception as e:
        messages.error(request, "An error occurred while loading the confirmation page.")
        print(f"Amount request confirmation error: {e}")
        return redirect("core_apps.account:dashboard")

@login_required
@kyc_required
def AmountRequestFinalProcess(request, account_number, transaction_id):
    """Finalize the payment request with PIN verification"""
    try:
        account = get_object_or_404(Account, account_number=account_number)
        transaction = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)
        
        # Validate transaction
        if transaction.receiver_account != account:
            messages.warning(request, "Invalid transaction.")
            return redirect("core_apps.account:dashboard")
        
        if transaction.status != "request_processing":
            messages.warning(request, "This request has already been processed.")
            return redirect("core_apps.account:dashboard")

        if request.method == "POST":
            pin_number = request.POST.get("pin-number", "").strip()
            
            if not pin_number:
                messages.warning(request, "Please enter your PIN.")
                return redirect("core_apps.core:amount-request-confirmation", account_number, transaction_id)

            if pin_number == request.user.account.pin_number:
                transaction.status = "request_sent"
                transaction.save()
                messages.success(request, "Your payment request has been sent successfully.")
                return redirect("core_apps.core:amount-request-completed", account.account_number, transaction.transaction_id)
            else:
                messages.warning(request, "Incorrect PIN.")
                return redirect("core_apps.core:amount-request-confirmation", account_number, transaction_id)
        else:
            messages.warning(request, "Invalid request method.")
            return redirect("core_apps.core:amount-request-confirmation", account_number, transaction_id)
    
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction or account not found.")
        return redirect("core_apps.account:dashboard")
    
    except Exception as e:
        messages.error(request, "An error occurred while processing your request.")
        print(f"Amount request final process error: {e}")
        return redirect("core_apps.core:amount-request-confirmation", account_number, transaction_id)

@login_required
@kyc_required
def RequestCompleted(request, account_number, transaction_id):
    """Display request completion page"""
    try:
        account = get_object_or_404(Account, account_number=account_number)
        transaction = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)
        
        # Verify transaction is in sent status
        if transaction.status != "request_sent":
            messages.warning(request, "Invalid request status.")
            return redirect("core_apps.account:dashboard")

        kyc = get_user_kyc(request.user)
        
        context = {
            "account": account,
            "transaction": transaction,
            "kyc": kyc,
        }
        return render(request, "payment_request/amount-request-completed.html", context)
    
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction or account not found.")
        return redirect("core_apps.account:dashboard")
    
    except Exception as e:
        messages.error(request, "An error occurred while loading the completion page.")
        print(f"Request completed error: {e}")
        return redirect("core_apps.account:dashboard")

@login_required
@kyc_required
def settlement_confirmation(request, account_number, transaction_id):
    """Display settlement confirmation page"""
    try:
        account = get_object_or_404(Account, account_number=account_number)
        transaction = get_object_or_404(Transaction, transaction_id=transaction_id, receiver=request.user)
        
        # Verify user is the receiver of the request
        if transaction.receiver != request.user:
            messages.warning(request, "You are not authorized to settle this request.")
            return redirect("core_apps.account:dashboard")
        
        if transaction.status != "request_sent":
            messages.warning(request, "This request cannot be settled.")
            return redirect("core_apps.account:dashboard")

        kyc = get_user_kyc(request.user)
        
        context = {
            "account": account,
            "transaction": transaction,
            "kyc": kyc,
        }
        return render(request, "payment_request/settlement-confirmation.html", context)
    
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction or account not found.")
        return redirect("core_apps.account:dashboard")
    
    except Exception as e:
        messages.error(request, "An error occurred while loading the settlement page.")
        print(f"Settlement confirmation error: {e}")
        return redirect("core_apps.account:dashboard")

@login_required
@kyc_required
def settlement_processing(request, account_number, transaction_id):
    """Process the settlement of a payment request"""
    try:
        account = get_object_or_404(Account, account_number=account_number)
        transaction = get_object_or_404(Transaction, transaction_id=transaction_id, receiver=request.user)
        
        sender = request.user
        sender_account = request.user.account

        # Validate authorization and status
        if transaction.receiver != request.user:
            messages.warning(request, "You are not authorized to settle this request.")
            return redirect("core_apps.account:dashboard")
        
        if transaction.status != "request_sent":
            messages.warning(request, "This request cannot be settled.")
            return redirect("core_apps.account:dashboard")

        if request.method == "POST":
            pin_number = request.POST.get("pin-number", "").strip()
            
            if not pin_number:
                messages.warning(request, "Please enter your PIN.")
                return redirect("core_apps.core:settlement-confirmation", account_number, transaction_id)

            if pin_number == sender_account.pin_number:
                # Check sufficient funds
                if sender_account.account_balance < transaction.amount:
                    messages.warning(request, "Insufficient funds. Please fund your account and try again.")
                    return redirect("core_apps.core:settlement-confirmation", account_number, transaction_id)
                
                # Process settlement
                sender_account.account_balance -= transaction.amount
                sender_account.save()

                account.account_balance += transaction.amount
                account.save()

                transaction.status = "request_settled"
                transaction.save()

                messages.success(request, f"Payment to {account.user.kyc.full_name} was successful.")
                return redirect("core_apps.core:settlement-completed", account.account_number, transaction.transaction_id)
            else:
                messages.warning(request, "Incorrect PIN.")
                return redirect("core_apps.core:settlement-confirmation", account_number, transaction.transaction_id)
        else:
            messages.warning(request, "Invalid request method.")
            return redirect("core_apps.core:settlement-confirmation", account_number, transaction.transaction_id)
    
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction or account not found.")
        return redirect("core_apps.account:dashboard")
    
    except Exception as e:
        messages.error(request, "An error occurred while processing the settlement.")
        print(f"Settlement processing error: {e}")
        return redirect("core_apps.core:settlement-confirmation", account_number, transaction_id)

@login_required
@kyc_required
def SettlementCompleted(request, account_number, transaction_id):
    """Display settlement completion page"""
    try:
        account = get_object_or_404(Account, account_number=account_number)
        transaction = get_object_or_404(Transaction, transaction_id=transaction_id, receiver=request.user)
        
        # Verify settlement was completed
        if transaction.status != "request_settled":
            messages.warning(request, "Settlement not completed.")
            return redirect("core_apps.account:dashboard")

        kyc = get_user_kyc(request.user)
        
        context = {
            "account": account,
            "transaction": transaction,
            "kyc": kyc,
        }
        return render(request, "payment_request/settlement-completed.html", context)
    
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction or account not found.")
        return redirect("core_apps.account:dashboard")
    
    except Exception as e:
        messages.error(request, "An error occurred while loading the completion page.")
        print(f"Settlement completed error: {e}")
        return redirect("core_apps.account:dashboard")

@login_required
@kyc_required
def DeletePaymentRequest(request, account_number, transaction_id):
    """Delete a payment request"""
    try:
        account = get_object_or_404(Account, account_number=account_number)
        transaction = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)
        
        # Verify user owns the transaction and it's in a deletable state
        if request.user == transaction.user and transaction.status in ["request_processing", "request_sent"]:
            transaction.delete()
            messages.success(request, "Payment Request Deleted Successfully.")
        else:
            messages.warning(request, "Cannot delete this payment request.")
        
        return redirect("core_apps.core:transactions")
    
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction or account not found.")
        return redirect("core_apps.core:transactions")
    
    except Exception as e:
        messages.error(request, "An error occurred while deleting the payment request.")
        print(f"Delete payment request error: {e}")
        return redirect("core_apps.core:transactions")

# CASHOUT PAYMENT REQUEST VIEWS
@login_required
@kyc_required
def payment_request_dashboard(request):
    """Main payment request dashboard"""
    try:
        kyc = get_user_kyc(request.user)
        account = get_user_account(request.user)
        
        if not account:
            messages.error(request, "Account not found.")
            return redirect("core_apps.account:dashboard")
        
        # Get user's payment requests
        payment_requests = PaymentRequest.objects.filter(user=request.user).order_by('-created_at')
        
        context = {
            'kyc': kyc,
            'account': account,
            'payment_requests': payment_requests,
        }
        return render(request, 'payment_request/dashboard.html', context)
    
    except Exception as e:
        messages.error(request, "An error occurred while loading the dashboard.")
        print(f"Payment request dashboard error: {e}")
        return redirect("core_apps.account:dashboard")

@login_required
@kyc_required
def create_payment_request(request):
    """Create new payment request"""
    try:
        if request.method == 'POST':
            form = PaymentRequestForm(request.POST, request.FILES)
            if form.is_valid():
                payment_request = form.save(commit=False)
                payment_request.user = request.user
                payment_request.save()
                
                messages.success(request, 'Payment request submitted successfully!')
                return redirect('core_apps.core:payment-request-dashboard')
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = PaymentRequestForm()
        
        kyc = get_user_kyc(request.user)
        account = get_user_account(request.user)
        
        if not account:
            messages.error(request, "Account not found.")
            return redirect("core_apps.account:dashboard")
        
        context = {
            'form': form,
            'kyc': kyc,
            'account': account,
        }
        return render(request, 'payment_request/create_request.html', context)
    
    except Exception as e:
        messages.error(request, "An error occurred while creating the payment request.")
        print(f"Create payment request error: {e}")
        return redirect('core_apps.core:payment-request-dashboard')

@login_required
def payment_request_list(request):
    """List all payment requests for admin"""
    if not request.user.is_staff:
        messages.warning(request, "Access denied. Admin privileges required.")
        return redirect('core_apps.core:payment-request-dashboard')
    
    try:
        payment_requests = PaymentRequest.objects.all().order_by('-created_at')
        
        context = {
            'payment_requests': payment_requests,
        }
        return render(request, 'payment_request/admin_list.html', context)
    
    except Exception as e:
        messages.error(request, "An error occurred while loading payment requests.")
        print(f"Payment request list error: {e}")
        return redirect('core_apps.core:payment-request-dashboard')

@login_required
def update_payment_request_status(request, request_id):
    """Update payment request status (admin only)"""
    if not request.user.is_staff:
        messages.warning(request, "Access denied. Admin privileges required.")
        return redirect('core_apps.core:payment-request-dashboard')
    
    try:
        payment_request = get_object_or_404(PaymentRequest, id=request_id)
        
        if request.method == 'POST':
            new_status = request.POST.get('status')
            if new_status in dict(PaymentRequest.STATUS_CHOICES):
                payment_request.status = new_status
                payment_request.save()
                messages.success(request, f'Payment request status updated to {new_status}.')
            else:
                messages.error(request, 'Invalid status.')
        
        return redirect('core_apps.core:payment-request-list')
    
    except PaymentRequest.DoesNotExist:
        messages.error(request, "Payment request not found.")
        return redirect('core_apps.core:payment-request-list')
    
    except Exception as e:
        messages.error(request, "An error occurred while updating the status.")
        print(f"Update payment request status error: {e}")
        return redirect('core_apps.core:payment-request-list')