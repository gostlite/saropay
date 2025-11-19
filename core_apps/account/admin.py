from django.contrib import admin
from core_apps.account.models import Account, KYC, Debt, DebtPayment
from import_export.admin import ImportExportModelAdmin


class AccountAdminModel(ImportExportModelAdmin):
    list_editable = ['account_status', 'account_balance']
    list_display = ['user', 'account_number' ,'account_status', 'account_balance', 'kyc_submitted', 'kyc_confirmed']
    list_filter = ['account_status']

class KYCAdmin(ImportExportModelAdmin):
    search_fields = ["full_name"]
    list_display = ['user', 'full_name']


#DEBT MANAGEMENT




@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = [
        'account', 
        'debt_type', 
        'total_amount', 
        'remaining_amount', 
        'interest_rate', 
        'status', 
        'due_date',
        'created_at'
    ]
    list_filter = [
        'debt_type', 
        'status', 
        'created_at', 
        'due_date'
    ]
    search_fields = [
        'account__account_number', 
        'account__user__kyc__full_name',
        'account__user__email'
    ]
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20
    
    fieldsets = (
        ('Account Information', {
            'fields': ('account',)
        }),
        ('Debt Details', {
            'fields': (
                'debt_type', 
                'total_amount', 
                'remaining_amount', 
                'interest_rate',
                'status'
            )
        }),
        ('Dates', {
            'fields': ('due_date', 'created_at', 'updated_at')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)  # Convert to list first
        if obj:  # editing an existing object
            readonly_fields.append('account')  # Use append method
        return readonly_fields

@admin.register(DebtPayment)
class DebtPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'debt',
        'amount',
        'payment_type',
        'status',
        'created_at'
    ]
    list_filter = [
        'payment_type',
        'status', 
        'created_at'
    ]
    search_fields = [
        'debt__account__account_number',
        'debt__account__user__kyc__full_name'
    ]
    readonly_fields = ['created_at']
    list_per_page = 20
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'debt',
                'amount',
                'payment_type',
                'status'
            )
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('debt__account__user__kyc')

# Optional: If you want to see debt information in the Account admin
from core_apps.account.models import Account

class DebtInline(admin.StackedInline):
    model = Debt
    can_delete = False
    verbose_name_plural = 'Debt Information'
    fields = [
        'debt_type',
        'total_amount',
        'remaining_amount', 
        'interest_rate',
        'status',
        'due_date'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request, obj=None):
        return False

# Uncomment if you want to add debt as inline to Account admin
# class AccountAdmin(admin.ModelAdmin):
#     inlines = [DebtInline]
# 
# admin.site.unregister(Account)  # If Account is already registered
# admin.site.register(Account, AccountAdmin)
admin.site.register(Account, AccountAdminModel)
admin.site.register(KYC, KYCAdmin)