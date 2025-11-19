from django import forms
from django.core.validators import FileExtensionValidator, MaxValueValidator
from core_apps.core.models import CreditCard, GrantApplication, LoanApplication, PaymentRequest

class CreditCardForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"Card Holder Name"}))
    number = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"Card Number"}))
    month = forms.IntegerField(widget=forms.NumberInput(attrs={"placeholder":"Expiry Month"}))
    year = forms.IntegerField(widget=forms.NumberInput(attrs={"placeholder":"Expiry Year"}))
    cvv = forms.IntegerField(widget=forms.NumberInput(attrs={"placeholder":"CVV"}))

    class Meta:
        model = CreditCard
        fields = ['name', 'number', 'month', 'year', 'cvv', 'card_type']

class LoanApplicationForm(forms.ModelForm):
    amount_range_min = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum amount'
        })
    )
    
    amount_range_max = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Maximum amount'
        })
    )
    
    # File fields with validation
    identification_image = forms.ImageField(
        required=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'webp'],
                message='Only JPG, JPEG, PNG, PDF, and WEBP files are allowed.'
            )
        ],
        widget=forms.FileInput(attrs={
            'class': 'form-control', 
            'required': 'required',
            'accept': '.jpg,.jpeg,.png,.pdf,.webp'
        })
    )
    
    proof_of_income = forms.ImageField(
        required=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'webp'],
                message='Only JPG, JPEG, PNG, PDF, and WEBP files are allowed.'
            )
        ],
        widget=forms.FileInput(attrs={
            'class': 'form-control', 
            'required': 'required',
            'accept': '.jpg,.jpeg,.png,.pdf,.webp'
        })
    )
    
    additional_documents = forms.ImageField(
        required=False,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'webp', 'doc', 'docx'],
                message='Only JPG, JPEG, PNG, PDF, WEBP, DOC, and DOCX files are allowed.'
            )
        ],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.jpg,.jpeg,.png,.pdf,.webp,.doc,.docx'
        })
    )
    
    class Meta:
        model = LoanApplication
        fields = [
            'full_name', 'tax_id', 'email', 'phone', 'loan_type',
            'amount_requested', 'amount_range_min', 'amount_range_max', 
            'reason', 'identification_image', 'proof_of_income', 
            'additional_documents'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'required': 'required'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'loan_type': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'amount_requested': forms.NumberInput(attrs={'class': 'form-control', 'required': 'required'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'required': 'required'}),
        }

    def clean_identification_image(self):
        image = self.cleaned_data.get('identification_image')
        if image:
            # Check file size (5MB limit)
            if image.size > 20 * 1024 * 1024:  # 5MB in bytes
                raise forms.ValidationError('Identification image size should not exceed 5MB.')
        return image

    def clean_proof_of_income(self):
        image = self.cleaned_data.get('proof_of_income')
        if image:
            # Check file size (5MB limit)
            if image.size > 20 * 1024 * 1024:  # 5MB in bytes
                raise forms.ValidationError('Proof of income file size should not exceed 5MB.')
        return image

    def clean_additional_documents(self):
        document = self.cleaned_data.get('additional_documents')
        if document:
            # Check file size (10MB limit for additional documents)
            if document.size > 10 * 1024 * 1024:  # 10MB in bytes
                raise forms.ValidationError('Additional documents file size should not exceed 10MB.')
        return document

    def clean(self):
        cleaned_data = super().clean()
        amount_min = cleaned_data.get('amount_range_min')
        amount_max = cleaned_data.get('amount_range_max')
        
        # Validate amount range
        if amount_min and amount_max:
            if amount_min > amount_max:
                raise forms.ValidationError({
                    'amount_range_min': 'Minimum amount cannot be greater than maximum amount.'
                })
            if amount_min < 0 or amount_max < 0:
                raise forms.ValidationError({
                    'amount_range_min': 'Amount values cannot be negative.'
                })
        
        return cleaned_data

class GrantApplicationForm(forms.ModelForm):
    amount_range_min = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum amount'
        })
    )
    
    amount_range_max = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Maximum amount'
        })
    )
    
    organization_name = forms.CharField(required=False)
    project_description = forms.CharField(required=False)
    
    # File fields with validation
    identification_image = forms.ImageField(
        required=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'webp'],
                message='Only JPG, JPEG, PNG, PDF, and WEBP files are allowed.'
            )
        ],
        widget=forms.FileInput(attrs={
            'class': 'form-control', 
            'required': 'required',
            'accept': '.jpg,.jpeg,.png,.pdf,.webp'
        })
    )
    
    proposal_document = forms.ImageField(
        required=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'webp', 'doc', 'docx'],
                message='Only JPG, JPEG, PNG, PDF, WEBP, DOC, and DOCX files are allowed.'
            )
        ],
        widget=forms.FileInput(attrs={
            'class': 'form-control', 
            'required': 'required',
            'accept': '.jpg,.jpeg,.png,.pdf,.webp,.doc,.docx'
        })
    )
    
    additional_documents = forms.ImageField(
        required=False,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'webp', 'doc', 'docx', 'xls', 'xlsx'],
                message='Only JPG, JPEG, PNG, PDF, WEBP, DOC, DOCX, XLS, and XLSX files are allowed.'
            )
        ],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.jpg,.jpeg,.png,.pdf,.webp,.doc,.docx,.xls,.xlsx'
        })
    )
    
    class Meta:
        model = GrantApplication
        fields = [
            'full_name', 'tax_id', 'email', 'phone', 'grant_type',
            'organization_name', 'amount_requested', 'amount_range_min', 
            'amount_range_max', 'reason', 'project_description',
            'identification_image', 'proposal_document', 'additional_documents'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'required': 'required'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'grant_type': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'organization_name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount_requested': forms.NumberInput(attrs={'class': 'form-control', 'required': 'required'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'required': 'required'}),
            'project_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean_identification_image(self):
        image = self.cleaned_data.get('identification_image')
        if image:
            # Check file size (5MB limit)
            if image.size > 20 * 1024 * 1024:  # 5MB in bytes
                raise forms.ValidationError('Identification image size should not exceed 5MB.')
        return image

    def clean_proposal_document(self):
        document = self.cleaned_data.get('proposal_document')
        if document:
            # Check file size (10MB limit for proposals)
            if document.size > 20 * 1024 * 1024:  # 10MB in bytes
                raise forms.ValidationError('Proposal document size should not exceed 10MB.')
        return document

    def clean_additional_documents(self):
        document = self.cleaned_data.get('additional_documents')
        if document:
            # Check file size (10MB limit for additional documents)
            if document.size > 10 * 1024 * 1024:  # 10MB in bytes
                raise forms.ValidationError('Additional documents file size should not exceed 10MB.')
        return document

    def clean(self):
        cleaned_data = super().clean()
        amount_min = cleaned_data.get('amount_range_min')
        amount_max = cleaned_data.get('amount_range_max')
        
        # Validate amount range
        if amount_min and amount_max:
            if amount_min > amount_max:
                raise forms.ValidationError({
                    'amount_range_min': 'Minimum amount cannot be greater than maximum amount.'
                })
            if amount_min < 0 or amount_max < 0:
                raise forms.ValidationError({
                    'amount_range_min': 'Amount values cannot be negative.'
                })
        
        return cleaned_data
    
class PaymentRequestForm(forms.ModelForm):
    class Meta:
        model = PaymentRequest
        fields = ['payment_type', 'reason', 'amount', 'payment_screenshot']
        widgets = {
            'payment_type': forms.RadioSelect(attrs={'class': 'payment-type-radio'}),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please describe the reason for this payment...'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount'
            }),
            'payment_screenshot': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }