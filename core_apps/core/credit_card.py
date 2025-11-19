from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core_apps.core.models import CreditCard
from core_apps.account.models import Account, KYC
from decimal import Decimal

@login_required
def card_detail(request, card_id):
    account = Account.objects.get(user=request.user)
    credit_card = CreditCard.objects.get(card_id=card_id, user=request.user)

    kyc = KYC.objects.get(user=request.user)

    context = {
        "account": account,
        "credit_card": credit_card,
        "kyc": kyc,
    }
    return render(request, "credit_detail/credit-detail.html", context)

def fund_credit_card(request, card_id):
    credit_card = CreditCard.objects.get(card_id=card_id, user=request.user)
    account = request.user.account

    if request.method == "POST":
        amount = request.POST.get("funding_amount")

        if Decimal(amount) <= account.account_balance:
            account.account_balance -= Decimal(amount)
            account.save()

            credit_card.amount += Decimal(amount)
            credit_card.save()

            messages.success(request, "Funding Successfull")
            return redirect("core_apps.core:card-detail", credit_card.card_id)
        else:
            messages.warning(request, "Insufficient Funds")
            return redirect("core_apps.core:card-detail", credit_card.card_id)


def withdraw_fund(request, card_id):
    account = Account.objects.get(user=request.user)
    credit_card = CreditCard.objects.get(card_id=card_id, user=request.user)

    if request.method == "POST":
        amount = request.POST.get("amount")

        if credit_card.amount >= Decimal(amount):
            account.account_balance += Decimal(amount)
            account.save()

            credit_card.amount -= Decimal(amount)
            credit_card.save()

            messages.success(request, "Withdraw Successful")
            return redirect("core_apps.core:card-detail", credit_card.card_id)
        else:
            messages.warning(request, "Insufficient Funds")
            return redirect("core_apps.core:card-detail", credit_card.card_id)

def delete_card(request, card_id):
    credit_card = CreditCard.objects.get(card_id=card_id, user=request.user)
    credit_card.delete()

    messages.success(request, "Card Deleted Successful")
    return redirect("core_apps.account:dashboard")
        