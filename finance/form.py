from django import forms
from .models import Transaction, Account


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["amount", "date", "account", "category", "description"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        customer = kwargs.pop("customer", None)
        super().__init__(*args, **kwargs)
        if customer is not None:
            self.fields["account"].queryset = Account.objects.filter(customer=customer)

from django import forms
from django.utils import timezone

class TransferForm(forms.Form):
    from_account = forms.ModelChoiceField(queryset=None)
    recipient_national_id = forms.CharField(max_length=50)
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    date = forms.DateField(initial=timezone.now().date, widget=forms.DateInput(attrs={"type": "date"}))
    memo = forms.CharField(max_length=255, required=False)

    def __init__(self, *args, **kwargs):
        accounts_qs = kwargs.pop("accounts_qs", None)
        super().__init__(*args, **kwargs)
        if accounts_qs is not None:
            self.fields["from_account"].queryset = accounts_qs