from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from finance.models import Customer, Account, LedgerAccount
from finance.services.ledger import post_journal_entry
from finance.services.exceptions import InsufficientFundsError
from finance.services.utils import mask_national_id

TRANSFERS_OUT_NAME = "Transfers Out"
TRANSFERS_IN_NAME = "Transfers In"


def get_or_create_system_accounts(customer: Customer):
    out_acc, _ = LedgerAccount.objects.get_or_create(
        customer=customer,
        name=TRANSFERS_OUT_NAME,
        defaults={"type": LedgerAccount.EXPENSE},
    )
    in_acc, _ = LedgerAccount.objects.get_or_create(
        customer=customer,
        name=TRANSFERS_IN_NAME,
        defaults={"type": LedgerAccount.INCOME},
    )
    return out_acc, in_acc


def get_recipient_default_account(recipient: Customer) -> Account:
    # MVP rule: first active account
    acc = recipient.accounts.filter(is_active=True).order_by("id").first()
    if not acc:
        raise ValueError("Recipient has no active account")
    return acc


def transfer_to_national_id(
    sender: Customer,
    from_account: Account,
    recipient_national_id: str,
    amount,
    date=None,
    memo="",
):
    amount = Decimal(amount)
    if amount <= 0:
        raise ValueError("Amount must be positive")

    if from_account.customer_id != sender.id:
        raise ValueError("Source account does not belong to sender")

    recipient_national_id = (recipient_national_id or "").strip()
    if not recipient_national_id:
        raise ValueError("Recipient national_id is required")
    masked = mask_national_id(recipient_national_id)
    memo = memo or f"Transfer to {masked}",

    if date is None:
        date = timezone.now().date()

    recipient = Customer.objects.filter(national_id=recipient_national_id).first()
    if recipient is None:
        raise ValueError("Recipient not found")

    if recipient.id == sender.id:
        raise ValueError("Cannot transfer to self")

    to_account = get_recipient_default_account(recipient)

    from_ledger = from_account.ledger_account
    to_ledger = to_account.ledger_account

    # System income/expense ledger accounts for transfers
    sender_out_ledger, _ = get_or_create_system_accounts(sender)
    recipient_in_ledger, _ = get_or_create_system_accounts(recipient)

    with transaction.atomic():
        # Concurrency locks (works best on Postgres/MySQL)
        locked = (
            LedgerAccount.objects.select_for_update()
            .filter(id__in=[from_ledger.id, to_ledger.id, sender_out_ledger.id, recipient_in_ledger.id])
        )
        list(locked)

        current_balance = from_ledger.balance()
        if amount > current_balance:
            raise InsufficientFundsError(balance=current_balance, amount=amount)

        # Sender entry: Expense (Transfers Out) + Credit from Asset
        post_journal_entry(
            customer=sender,
            date=date,
            memo=memo or f"Transfer to {recipient_national_id}",
            lines=[
                {"account": sender_out_ledger, "debit": amount, "credit": 0},
                {"account": from_ledger, "debit": 0, "credit": amount},
            ],
        )

        # Recipient entry: Debit to Asset + Income (Transfers In)
        post_journal_entry(
            customer=recipient,
            date=date,
            memo=memo or f"Transfer from {sender.id}",
            lines=[
                {"account": to_ledger, "debit": amount, "credit": 0},
                {"account": recipient_in_ledger, "debit": 0, "credit": amount},
            ],
        )
