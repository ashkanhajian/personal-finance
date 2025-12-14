from rest_framework import serializers
from finance.models import Account, Transaction


class AccountSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ["id", "name", "currency", "is_active", "balance"]

    def get_balance(self, obj):
        # اگر Ledger وصل باشد، موجودی واقعی را از ledger بخوان
        if hasattr(obj, "ledger_account") and obj.ledger_account_id:
            return obj.ledger_account.balance()
        return None


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["id", "amount", "date", "account", "category", "description"]
