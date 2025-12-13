from django.db import transaction
from decimal import Decimal
from finance.models import JournalEntry, LedgerLine

def post_journal_entry(customer, date, memo, lines):
    """
    lines = [
        {"account": ledger_account, "debit": 100, "credit": 0},
        {"account": ledger_account, "debit": 0, "credit": 100},
    ]
    """
    total_debit = sum(Decimal(l["debit"]) for l in lines)
    total_credit = sum(Decimal(l["credit"]) for l in lines)

    if total_debit != total_credit:
        raise ValueError("Journal entry is not balanced")

    with transaction.atomic():
        entry = JournalEntry.objects.create(
            customer=customer,
            date=date,
            memo=memo,
        )
        for l in lines:
            LedgerLine.objects.create(
                entry=entry,
                account=l["account"],
                debit=l["debit"],
                credit=l["credit"],
            )
    return entry
