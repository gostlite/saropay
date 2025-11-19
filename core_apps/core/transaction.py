from django.shortcuts import render
from core_apps.core.models import Transaction
from core_apps.account.models import KYC
from django.contrib.auth.decorators import login_required


@login_required
def transaction_lists(request):
    sender_transaction = Transaction.objects.filter(sender=request.user, transaction_type="transfer").order_by("-id")
    receiver_transaction = Transaction.objects.filter(receiver=request.user, transaction_type="transfer").order_by("-id")

    request_sender_transaction = Transaction.objects.filter(sender=request.user, transaction_type="request")
    request_receiver_transactiion = Transaction.objects.filter(receiver=request.user, transaction_type="request")

    kyc = KYC.objects.get(user=request.user)


    context = {
        "sender_transaction": sender_transaction,
        "receiver_transaction": receiver_transaction,

        "request_sender_transaction": request_sender_transaction,
        "request_receiver_transactiion": request_receiver_transactiion,
        "kyc": kyc,
    }

    return render(request, "transaction/transaction-list.html", context)

@login_required
def transaction_detail(request, transaction_id):
    transaction = Transaction.objects.get(transaction_id=transaction_id)

    kyc = KYC.objects.get(user=request.user)

    context = {
        "transaction": transaction,
        "kyc": kyc,
    }

    return render(request, "transaction/transaction-detail.html", context)