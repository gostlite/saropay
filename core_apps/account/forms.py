from django import forms
from core_apps.account.models import KYC
from django.forms import ImageField, FileInput, DateInput

class DateInput(forms.DateInput):
    """Help user select date."""
    input_type = 'date'


class KYCForm(forms.ModelForm):
    identity_image = ImageField(widget=FileInput)
    image = ImageField(widget=FileInput)
    signature = ImageField(widget=FileInput)

    class Meta:
        model = KYC
        fields = [
            'full_name',
            'image',
            'marital_status',
            'gender',
            'identity_type',
            'identity_image',
            'date_of_birth',
            'signature',
            'country',
            'state',
            'city',
            'mobile',
            'fax',
        ]
        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "placeholder": "Full Name",
                }
            ),
            "mobile": forms.TextInput(
                attrs={
                    "placeholder": "Mobile Number",
                }
            ),
            "fax": forms.TextInput(
                attrs={
                    "placeholder": "Fax Number",
                    "class":"",
                    "id":"",
                }
            ),
            "country": forms.TextInput(attrs={"placeholder": "Country",}),
            "state": forms.TextInput(attrs={"placeholder": "State",}),
            "city": forms.TextInput(attrs={"placeholder": "City",}),
            "date_of_birth": DateInput      
        }