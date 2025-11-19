from django.urls import path
from core_apps.core import funding, subscription, views, transfer, transaction, payment_request, credit_card


app_name = "core_apps.core"

urlpatterns = [
    path("", views.index, name="index"),

    # Transfer
    path("search-account/", transfer.search_users_account_number, name="search-account"),
    path("amount-transfer/<account_number>/", transfer.AmountTransfer, name="amount-transfer"),
    path("amount-transfer-process/<account_number>/", transfer.AmountTransferProcess, name="amount-transfer-process"),
    path("transfer-confirmation/<account_number>/<transaction_id>/", transfer.TransferConfirmation, name="transfer-confirmation"),
    path("transfer-process/<account_number>/<transaction_id>/", transfer.TransferProcess, name="transfer-process"),
    path("transfer-completed/<account_number>/<transaction_id>/", transfer.TransferComplete, name="transfer-completed"),

    # Transactions
    path("transactions/", transaction.transaction_lists, name="transactions"),
    path("transaction-detail/<transaction_id>", transaction.transaction_detail, name="transaction-detail"),

    # Payment Request
    path("request-search-account/", payment_request.SearchUsersRequest, name="request-search-account"),
    path("amount-request/<account_number>/", payment_request.AmountRequest, name="amount-request"),
    path("amount-request-process/<account_number>/", payment_request.AmountRequestProcess, name="amount-request-process"),
    path("amount-request-confirmation/<account_number>/<transaction_id>/", payment_request.AmountRequestConfirmation, name="amount-request-confirmation"),
    path("amount-request-final-process/<account_number>/<transaction_id>/", payment_request.AmountRequestFinalProcess, name="amount-request-final-process"),
    path("amount-request-completed/<account_number>/<transaction_id>/", payment_request.RequestCompleted, name="amount-request-completed"),

    # Payment Request URLs
    path('payment-request/dashboard/', payment_request.payment_request_dashboard, name='payment-request-dashboard'),
    path('payment-request/create/', payment_request.create_payment_request, name='create-payment-request'),
    path('payment-request/list/', payment_request.payment_request_list, name='payment-request-list'),
    path('payment-request/update-status/<int:request_id>/', payment_request.update_payment_request_status, name='update-payment-status'),

    # Request Settlement
    path("settlement-confirmation/<account_number>/<transaction_id>/", payment_request.settlement_confirmation, name="settlement-confirmation"),
    path("settlement-processing/<account_number>/<transaction_id>/", payment_request.settlement_processing, name="settlement-processing"),
    path("settlement-completed/<account_number>/<transaction_id>/", payment_request.SettlementCompleted, name="settlement-completed"),
    path("delete-request/<account_number>/<transaction_id>/", payment_request.DeletePaymentRequest, name="delete-request"),

    # Credit Card
    path("card/<card_id>/", credit_card.card_detail, name="card-detail"),
    path("fund-credit-card/<card_id>/", credit_card.fund_credit_card, name="fund-credit-card"),
    path("withdraw_fund/<card_id>/", credit_card.withdraw_fund, name="withdraw_fund"),
    path("delete_card/<card_id>/", credit_card.delete_card, name="delete_card"),


    #subscription
    path('subscription-plans/', subscription.subscription_plans, name='subscription-plans'),
    # path('subscribe/<int:plan_id>/', subscription.create_checkout_session, name='subscribe'),
    # path('success/', subscription.subscription_success, name='success'),
    # path('cancel/', subscription.cancel_subscription, name='cancel'),

    #Funding url
    path('application/funding/', funding.funding_application, name='application'),
    path('submit-loan/', funding.submit_loan_application, name='submit-loan'),
    path('submit-grant/', funding.submit_grant_application, name='submit-grant'),
    path('application-status/', funding.application_status, name='application-status'),
    path('submitted/<str:app_type>/<int:app_id>/', funding.application_submitted, name='application-submitted'),
]