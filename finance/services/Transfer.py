from decimal import Decimal
from django.db import transaction

from finance.services.ledger import post_journal_entry
from finance.services.exceptions import InsufficientFundsError
from finance.models import LedgerAccount

def transfer_funds(customer, from_account, to_account, amount, date, memo=""):
    amount = Decimal(amount)

    if from_account == to_account:
        raise ValueError("Source and destination accounts must be different")
    if amount <= 0:
        raise ValueError("Amount must be positive")

    if from_account.customer_id != customer.id or to_account.customer_id != customer.id:
        raise ValueError("Accounts do not belong to this customer")

    from_ledger = from_account.ledger_account
    to_ledger = to_account.ledger_account

    with transaction.atomic():
        # Lock accounts for concurrency safety (works best on Postgres/MySQL)
        locked = (
            LedgerAccount.objects.select_for_update()
            .filter(id__in=[from_ledger.id, to_ledger.id])
        )
        list(locked)

        current_balance = from_ledger.balance()
        if amount > current_balance:
            raise InsufficientFundsError(balance=current_balance, amount=amount)

        lines = [
            {"account": to_ledger, "debit": amount, "credit": 0},
            {"account": from_ledger, "debit": 0, "credit": amount},
        ]

        entry = post_journal_entry(
            customer=customer,
            date=date,
            memo=memo or f"Transfer {amount}",
            lines=lines,
        )
        return entry
