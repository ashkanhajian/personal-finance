from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from finance.models import Account, Transaction
from finance.api.serializers import AccountSerializer, TransactionSerializer
from finance.api.permissions import IsCustomerOwner
from finance.services.exceptions import InsufficientFundsError
from finance.services.inter_customer_transfers import transfer_to_national_id


class AccountViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AccountSerializer

    def get_queryset(self):
        customer = getattr(self.request.user, "customer_profile", None)
        if customer is None:
            return Account.objects.none()
        return Account.objects.filter(customer=customer, is_active=True).order_by("name")


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        customer = getattr(self.request.user, "customer_profile", None)
        if customer is None:
            return Transaction.objects.none()
        return Transaction.objects.filter(account__customer=customer).order_by("-date", "-created_at")

    def perform_create(self, serializer):
        # اطمینان: فقط روی حساب‌های خودش بتواند Transaction بسازد
        customer = getattr(self.request.user, "customer_profile", None)
        account = serializer.validated_data["account"]
        if customer is None or account.customer_id != customer.id:
            raise PermissionError("Invalid account")
        serializer.save()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def transfer_api(request):
    """
    POST payload:
    {
      "from_account_id": 1,
      "recipient_national_id": "....",
      "amount": "100.00",
      "date": "2025-12-14",
      "memo": "optional"
    }
    """
    customer = getattr(request.user, "customer_profile", None)
    if customer is None:
        return Response({"detail": "Customer profile not found."}, status=status.HTTP_400_BAD_REQUEST)

    from_account_id = request.data.get("from_account_id")
    recipient_national_id = request.data.get("recipient_national_id")
    amount = request.data.get("amount")
    date = request.data.get("date")
    memo = request.data.get("memo", "")

    try:
        from_account = Account.objects.get(id=from_account_id, customer=customer, is_active=True)
    except Account.DoesNotExist:
        return Response({"detail": "Invalid source account."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        transfer_to_national_id(
            sender=customer,
            from_account=from_account,
            recipient_national_id=recipient_national_id,
            amount=amount,
            date=date,
            memo=memo,
        )
        return Response({"detail": "Transfer completed."}, status=status.HTTP_201_CREATED)
    except InsufficientFundsError:
        return Response({"detail": "Insufficient funds."}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({"detail": "Transfer failed. Check recipient and inputs."}, status=status.HTTP_400_BAD_REQUEST)
