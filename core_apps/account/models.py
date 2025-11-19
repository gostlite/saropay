from django.db import models
import uuid
from shortuuid.django_fields import ShortUUIDField
from core_apps.userauths.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
# from django_countries.fields import CountryField
# from phonenumber_field.modelfields import PhoneNumberField

ACCOUNT_STATUS = (
    ("active", "Active"),
    ("pending", "Pending"),
    ("in-active", "In-active"),
)

MARITAL_STATUS = (
    ("married", "Married"),
    ("single", "Single"),
    ("other", "Other"),
)

GENDER = (
    ("male", "Male"),
    ("female", "Female"),
    ("other", "Other"),
)

# NATIONALITY = (
#     ("ghana", "Ghana"),
#     ("nigeia", "Nigeia"),
#     ("kenya", "Kenya"),
# )

IDENTITY_TYPE = (
    ("national_id_card", "National ID Card"),
    ("drivers_licence", "Drivers Licence"),
    ("international_passport", "International Passport"),
)

def user_directory_path(instance, filename):
    """File uploads."""
    ext = filename.split(".")[-1]
    filename = "%s_%s" % (instance.id, ext)
    return "user_{0}/{1}".format(instance.user.id, filename)

class Account(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    account_number = ShortUUIDField(unique=True, length=10, max_length=25, prefix="004", alphabet="1234567890")
    account_id = ShortUUIDField(unique=True, length=7, max_length=25, prefix="DEX", alphabet="1234567890")
    pin_number = ShortUUIDField(unique=True, length=4, max_length=7, alphabet="1234567890")
    ref_code = ShortUUIDField(unique=True, length=10, max_length=20, alphabet="abcdefgh1234567890")
    account_status = models.CharField(max_length=100, choices=ACCOUNT_STATUS, default="in-active")
    date = models.DateTimeField(auto_now_add=True)
    kyc_submitted = models.BooleanField(default=False)
    kyc_confirmed = models.BooleanField(default=False)
    recommended_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name="recommended_by")

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user}"

class KYC(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account = models.OneToOneField(Account, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=1000)
    image = models.ImageField(upload_to="kyc", default="default.jpg")
    marital_status = models.CharField(choices=MARITAL_STATUS, max_length=40)
    gender = models.CharField(choices=GENDER, max_length=40)
    identity_type = models.CharField(choices=IDENTITY_TYPE, max_length=140)
    identity_image = models.ImageField(upload_to="kyc", blank=True, null=True)
    date_of_birth = models.DateTimeField(auto_now_add=False)
    signature = models.ImageField(upload_to="kyc", default="default.jpg")

    """Address"""
    country = models.CharField(max_length=1000)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    """Contact Detail"""
    mobile = models.CharField(max_length=1000)
    fax = models.CharField(max_length=1000)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}"

def create_account(sender, instance, created, **kwargs):
    """Create bank account."""
    if created:
        Account.objects.create(user=instance)
    
def save_account(sender, instance, **kwargs):
    """Save bank account."""
    instance.account.save()



#DEBT PAYMENT

class Debt(models.Model):
    DEBT_TYPES = (
        ('loan', 'Loan Application'),
        ('grant', 'Grant Application'),
        ('personal', 'Charity Fee'),
        ('interest', 'Share Payment'),
        ('delivery', 'Delivery'),
        # ('medical', 'Medical'),
        # ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('settled', 'Settled'),
    )
    
    account = models.OneToOneField(
        Account, 
        on_delete=models.CASCADE, 
        related_name='debt'
    )
    debt_type = models.CharField(max_length=20, choices=DEBT_TYPES, default='personal')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Debt"
        verbose_name_plural = "Debts"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.account.user.kyc.full_name} - {self.get_debt_type_display()} - ${self.remaining_amount}"
    
    @property
    def amount_paid(self):
        """Calculate total amount paid towards debt"""
        return self.total_amount - self.remaining_amount
    
    @property
    def repayment_percentage(self):
        """Calculate repayment progress percentage"""
        if self.total_amount > 0:
            return round((self.amount_paid / self.total_amount) * 100, 2)
        return 0
    
    @property
    def is_overdue(self):
        """Check if debt is overdue"""
        if self.due_date and timezone.now().date() > self.due_date:
            return True
        return False
    
    def save(self, *args, **kwargs):
        """Update status based on conditions"""
        if self.remaining_amount <= 0:
            self.status = 'paid'
        elif self.is_overdue:
            self.status = 'overdue'
        super().save(*args, **kwargs)


class DebtPayment(models.Model):
    PAYMENT_TYPES = (
        ('installment', 'Installment'),
        ('lump_sum', 'Lump Sum'),
        ('settlement', 'Settlement'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    debt = models.ForeignKey(Debt, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_type = models.CharField(max_length=15, choices=PAYMENT_TYPES, default='installment')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='completed')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment of ${self.amount} for {self.debt}"


@receiver(post_save, sender=Account)
def create_debt_for_account(sender, instance, created, **kwargs):
    """
    Signal to automatically create a Debt instance when a new Account is created
    """
    if created:
        Debt.objects.create(account=instance)

@receiver(post_save, sender=Account)
def save_debt_for_account(sender, instance, **kwargs):
    """
    Signal to save Debt instance when Account is saved
    """
    if hasattr(instance, 'debt'):
        instance.debt.save()
post_save.connect(create_account, sender=User)
post_save.connect(save_account, sender=User)