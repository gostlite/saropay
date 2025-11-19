from django.utils import timezone
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from core_apps.userauths.models import User
from core_apps.account.models import Account
from shortuuid.django_fields import ShortUUIDField


TRANSACTION_TYPE = (
    ("transfer", "Transfer"),
    ("recieved", "Recieved"),
    ("withdraw", "Withdraw"),
    ("refund", "Refund"),
    ("request", "Payment Request"),
    ("none", "None")
)

TRANSACTION_STATUS = (
    ("failed", "Failed"),
    ("completed", "Completed"),
    ("pending", "Pending"),
    ("processing", "Processing"),
    ("request_sent", "Requested Sent"),
    ("requested_settled", "Requested Settled"),
    ("request_processing", "Request Processing"),
)


CARD_TYPE = (
    ("master", "Master Card"),
    ("visa", "Visa Card"),
    ("verve", "Verve Card"),
)

class Transaction(models.Model):
    transaction_id = ShortUUIDField(unique=True, length=15, max_length=20, prefix="TRN")
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="user")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    description = models.CharField(max_length=1000, null=True, blank=True)

    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="receiver")
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="sender")

    receiver_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name="receiver_account")
    sender_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name="sender_account")

    status = models.CharField(choices=TRANSACTION_STATUS, max_length=100, default="none")
    transaction_type = models.CharField(choices=TRANSACTION_TYPE, max_length=100, default="none")

    date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=False, null=True, blank=True)

    def __str__(self):
        try:
            return f"{self.user}"
        except:
            return f"Transaction"


class CreditCard(models.Model):
    """Credit card."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card_id = ShortUUIDField(unique=True, length=5, max_length=20, prefix="CARD", alphabet="1234567890")

    name = models.CharField(max_length=100)
    number = models.CharField(max_length=20)
    month = models.IntegerField()
    year = models.IntegerField()
    cvv = models.IntegerField()

    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    card_type = models.CharField(choices=CARD_TYPE, max_length=20, default="master")
    card_status = models.BooleanField(default=True)

    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}"
    

#SUBSCRIRPTION MODEL

class SubscriptionPlan(models.Model):
    PLAN_TYPES = [
        ('FREE', 'Free'),
        ('BASIC', 'Basic'),
        ('GOLD', 'Gold'),
        ('PREMIUM', 'Premium'),
    ]
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    billing_cycle = models.CharField(max_length=20, default='monthly')
    description = models.TextField(blank=True)
    
    # Features
    max_projects = models.IntegerField(default=3)
    has_analytics = models.BooleanField(default=False)
    has_priority_support = models.BooleanField(default=False)
    has_custom_branding = models.BooleanField(default=False)
    has_api_access = models.BooleanField(default=False)
    has_dedicated_manager = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - ${self.price}/{self.billing_cycle}"

class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    
    is_active = models.BooleanField(default=False)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def is_valid(self):
        if not self.is_active:
            return False
        if self.current_period_end and timezone.now() > self.current_period_end:
            return False
        return True
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name if self.plan else 'No Plan'}"



class LoanApplication(models.Model):
    LOAN_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review'),
    ]
    
    LOAN_TYPES = [
        ('personal', 'Personal Loan'),
        ('business', 'Business Loan'),
        ('education', 'Education Loan'),
        ('mortgage', 'Mortgage'),
        ('emergency', 'Emergency Loan'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPES, default='personal')
    amount_requested = models.DecimalField(max_digits=12, decimal_places=2)
    amount_range_min = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_range_max = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reason = models.TextField()
    
    # Supporting documents
    identification_image = models.ImageField(upload_to='loans/identification/')
    proof_of_income = models.ImageField(upload_to='loans/income_proof/')
    additional_documents = models.ImageField(upload_to='loans/additional/', blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=LOAN_STATUS, default='pending')
    application_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.amount_requested} - {self.status}"

class GrantApplication(models.Model):
    GRANT_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review'),
    ]
    
    GRANT_TYPES = [
        ('education', 'Education Grant'),
        ('research', 'Research Grant'),
        ('business', 'Business Grant'),
        ('community', 'Community Project Grant'),
        ('nonprofit', 'Non-Profit Grant'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    grant_type = models.CharField(max_length=20, choices=GRANT_TYPES, default='education')
    organization_name = models.CharField(max_length=255, blank=True)
    amount_requested = models.DecimalField(max_digits=12, decimal_places=2)
    amount_range_min = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_range_max = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reason = models.TextField()
    project_description = models.TextField(blank=True)
    
    # Supporting documents
    identification_image = models.ImageField(upload_to='grants/identification/')
    proposal_document = models.ImageField(upload_to='grants/proposals/')
    additional_documents = models.ImageField(upload_to='grants/additional/', blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=GRANT_STATUS, default='pending')
    application_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.amount_requested} - {self.status}"



class PaymentRequest(models.Model):
    PAYMENT_TYPES = [
        ('subscription', 'Subscription'),
        ('charity', 'Charity'), 
        ('others', 'Others'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    reason = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_screenshot = models.ImageField(upload_to='payment_screenshots/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.payment_type} - ${self.amount}"



