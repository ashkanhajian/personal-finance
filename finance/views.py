from django.shortcuts import render
from django.db.models import Sum
from .models import Transaction, Category


def dashboard(request):
    income_total = (
        Transaction.objects
        .filter(category__type=Category.INCOME)
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    expense_total = (
        Transaction.objects
        .filter(category__type=Category.EXPENSE)
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    transactions = (
        Transaction.objects
        .select_related("category", "account")
        .order_by("-date", "-created_at")[:20]
    )

    net_total = income_total - expense_total

    context = {
        "income_total": income_total,
        "expense_total": expense_total,
        "net_total": net_total,
        "transactions": transactions
    }
    return render(request, "finance/dashboard.html", context)
