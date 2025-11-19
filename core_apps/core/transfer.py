from django.shortcuts import render, redirect, get_object_or_404
from core_apps.account.models import Account, KYC
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from core_apps.core.models import Transaction
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

@login_required
@kyc_required
def search_users_account_number(request):
    """Search for users by account number"""
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
            "accounts": accounts,  # Changed from "account" to "accounts" for clarity
            "query": query,
            "kyc": kyc,
        }
        return render(request, "transfer/search-user-account-number.html", context)
    
    except Exception as e:
        messages.error(request, "An error occurred while searching for accounts.")
        print(f"Search account error: {e}")
        return redirect("core_apps.account:dashboard")

@login_required
@kyc_required
def AmountTransfer(request, account_number):
    """Display amount transfer page for a specific account"""
    try:
        kyc = get_user_kyc(request.user)
        account = get_object_or_404(Account, account_number=account_number)
        
        # Prevent self-transfer
        if account.user == request.user:
            messages.warning(request, "You cannot transfer money to your own account.")
            return redirect("core_apps.core:search-account")
        
        context = {
            "account": account,
            "kyc": kyc,
        }
        return render(request, "transfer/amount-transfer.html", context)
    
    except Account.DoesNotExist:
        messages.warning(request, "Account does not exist.")
        return redirect("core_apps.core:search-account")
    
    except Exception as e:
        messages.error(request, "An error occurred while loading the transfer page.")
        print(f"Amount transfer error: {e}")
        return redirect("core_apps.core:search-account")

@login_required
@kyc_required
def AmountTransferProcess(request, account_number):
    """Process the amount transfer request"""
    try:
        # Get accounts
        receiver_account = get_object_or_404(Account, account_number=account_number)
        sender_account = request.user.account
        
        # Prevent self-transfer
        if receiver_account.user == request.user:
            messages.warning(request, "You cannot transfer money to your own account.")
            return redirect("core_apps.core:search-account")

        if request.method == "POST":
            amount_str = request.POST.get("amount-send", "").strip()
            description = request.POST.get("description", "").strip()

            # Validate amount
            if not amount_str:
                messages.warning(request, "Please enter an amount.")
                return redirect("core_apps.core:amount-transfer", account_number)
            
            try:
                amount = Decimal(amount_str)
                if amount <= 0:
                    messages.warning(request, "Amount must be greater than zero.")
                    return redirect("core_apps.core:amount-transfer", account_number)
            except (InvalidOperation, ValueError):
                messages.warning(request, "Invalid amount format.")
                return redirect("core_apps.core:amount-transfer", account_number)

            # Check if sender has sufficient funds
            if sender_account.account_balance >= amount:
                # Create transaction record
                new_transaction = Transaction.objects.create(
                    user=request.user,
                    amount=amount,
                    description=description,
                    receiver=receiver_account.user,
                    sender=request.user,
                    sender_account=sender_account,
                    receiver_account=receiver_account,
                    status="processing",
                    transaction_type="transfer"
                )
                
                transaction_id = new_transaction.transaction_id
                return redirect("core_apps.core:transfer-confirmation", account_number, transaction_id)
            else:
                messages.warning(request, "Insufficient funds.")
                return redirect("core_apps.core:amount-transfer", account_number)
        else:
            messages.warning(request, "Invalid request method.")
            return redirect("core_apps.core:amount-transfer", account_number)
    
    except Account.DoesNotExist:
        messages.warning(request, "Account does not exist.")
        return redirect("core_apps.core:search-account")
    
    except Exception as e:
        messages.error(request, "An error occurred while processing the transfer.")
        print(f"Amount transfer process error: {e}")
        return redirect("core_apps.core:amount-transfer", account_number)

@login_required
@kyc_required
def TransferConfirmation(request, account_number, transaction_id):
    """Display transfer confirmation page"""
    try:
        kyc = get_user_kyc(request.user)
        account = get_object_or_404(Account, account_number=account_number)
        transaction = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)
        
        # Verify transaction belongs to current user and matches the account
        if transaction.receiver_account != account:
            messages.warning(request, "Invalid transaction.")
            return redirect("core_apps.account:account")

        context = {
            "account": account,
            "transaction": transaction,
            "kyc": kyc,
        }
        return render(request, "transfer/transfer-confirmation.html", context)
    
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction or account not found.")
        return redirect("core_apps.account:account")
    
    except Exception as e:
        messages.error(request, "An error occurred while loading the confirmation page.")
        print(f"Transfer confirmation error: {e}")
        return redirect("core_apps.account:account")

@login_required
@kyc_required
def TransferProcess(request, account_number, transaction_id):
    """Process the final transfer with PIN verification"""
    try:
        account = get_object_or_404(Account, account_number=account_number)
        transaction = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)
        
        sender_account = request.user.account
        receiver_account = account

        # Validate transaction ownership and status
        if transaction.receiver_account != receiver_account:
            messages.warning(request, "Invalid transaction.")
            return redirect("core_apps.account:account")
        
        if transaction.status != "processing":
            messages.warning(request, "This transaction has already been processed.")
            return redirect("core_apps.account:account")

        if request.method == "POST":
            pin_number = request.POST.get("pin-number", "").strip()

            if not pin_number:
                messages.warning(request, "Please enter your PIN.")
                return redirect('core_apps.core:transfer-confirmation', account_number, transaction_id)

            # Validate PIN number
            if pin_number == sender_account.pin_number:
                try:
                    # Update transaction status
                    transaction.status = "completed"
                    transaction.save()

                    # Update account balances
                    sender_account.account_balance -= transaction.amount
                    sender_account.save()

                    receiver_account.account_balance += transaction.amount
                    receiver_account.save()

                    messages.success(request, "Transfer completed successfully!")
                    return redirect("core_apps.core:transfer-completed", account_number, transaction_id)
                
                except Exception as e:
                    # Rollback transaction status if balance update fails
                    transaction.status = "failed"
                    transaction.save()
                    messages.error(request, "Transfer failed due to a system error.")
                    print(f"Balance update error: {e}")
                    return redirect('core_apps.core:transfer-confirmation', account_number, transaction_id)
            
            else:
                messages.warning(request, "Incorrect PIN.")
                return redirect('core_apps.core:transfer-confirmation', account_number, transaction_id)
        else:
            messages.warning(request, "Invalid request method.")
            return redirect("core_apps.core:transfer-confirmation", account_number, transaction_id)
    
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction or account not found.")
        return redirect("core_apps.account:account")
    
    except Exception as e:
        messages.error(request, "An error occurred while processing the transfer.")
        print(f"Transfer process error: {e}")
        return redirect("core_apps.core:transfer-confirmation", account_number, transaction_id)

@login_required
@kyc_required
def TransferComplete(request, account_number, transaction_id):
    """Display transfer completion page"""
    try:
        kyc = get_user_kyc(request.user)
        account = get_object_or_404(Account, account_number=account_number)
        transaction = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)
        
        # Verify transaction is completed and belongs to user
        if transaction.status != "completed" or transaction.receiver_account != account:
            messages.warning(request, "Invalid completed transaction.")
            return redirect("core_apps.account:account")

        context = {
            "account": account,
            "transaction": transaction,
            "kyc": kyc,
        }
        return render(request, "transfer/transfer-completed.html", context)
    
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction or account not found.")
        return redirect("core_apps.account:account")
    
    except Exception as e:
        messages.error(request, "An error occurred while loading the completion page.")
        print(f"Transfer complete error: {e}")
        return redirect("core_apps.account:account")