from django.contrib import admin
from core_apps.core.models import GrantApplication, LoanApplication, PaymentRequest, SubscriptionPlan, Transaction, CreditCard, UserSubscription

class TransactionAdmin(admin.ModelAdmin):
    list_editable = ['amount', 'status', 'transaction_type', 'receiver', 'sender']
    list_display = ['user', 'amount', 'status', 'transaction_type', 'receiver', 'sender']

class CreditCardAdmin(admin.ModelAdmin):
    list_editable = ['amount', 'card_type']
    list_display = ['user', 'amount', 'card_type']


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price', 'billing_cycle', 'is_active']
    list_filter = ['plan_type', 'is_active']
    search_fields = ['name', 'plan_type']

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'is_active', 'current_period_end', 'created_at']
    list_filter = ['is_active', 'plan']
    search_fields = ['user__username', 'user__email']

@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'loan_type', 'amount_requested', 'status', 'application_date']
    list_filter = ['status', 'loan_type', 'application_date']
    search_fields = ['full_name', 'email', 'tax_id']
    readonly_fields = ['application_date', 'updated_at']

@admin.register(GrantApplication)
class GrantApplicationAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'grant_type', 'amount_requested', 'status', 'application_date']
    list_filter = ['status', 'grant_type', 'application_date']
    search_fields = ['full_name', 'email', 'tax_id', 'organization_name']
    readonly_fields = ['application_date', 'updated_at']



@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'payment_type', 'amount', 'status', 'created_at']
    list_filter = ['payment_type', 'status', 'created_at']
    search_fields = ['user__username', 'reason']
    readonly_fields = ['created_at', 'updated_at']


    
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(CreditCard, CreditCardAdmin)