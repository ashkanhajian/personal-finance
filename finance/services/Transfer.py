from finance.services.ledger import post_journal_entry

def transfer_funds(customer, from_account, to_account, amount, date, memo=""):
    if from_account == to_account:
        raise ValueError("Source and destination accounts must be different")

    from_ledger = from_account.ledger_account
    to_ledger = to_account.ledger_account

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
