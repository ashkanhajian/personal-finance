from django.shortcuts import render, redirect
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from .form import TransactionForm
from .models import Transaction, Category, Account

def get_current_customer(user):
    return getattr(user, "customer_profile", None)


@login_required
def dashboard(request):
    customer = get_current_customer(request.user)
    if customer is None:
        # فعلاً ساده: اگر Customer نداشت، داشبورد خالی نشان بده
        transactions = Transaction.objects.none()
        income_total = 0
        expense_total = 0
    else:
        qs = Transaction.objects.filter(account__customer=customer)

        income_total = (
            qs.filter(category__type=Category.INCOME)
            .aggregate(total=Sum("amount"))["total"]
            or 0
        )

        expense_total = (
            qs.filter(category__type=Category.EXPENSE)
            .aggregate(total=Sum("amount"))["total"]
            or 0
        )

        transactions = (
            qs.select_related("category", "account")
            .order_by("-date", "-created_at")[:20]
        )

    net_total = income_total - expense_total

    expense_by_category = (
        transactions.filter(category__type=Category.EXPENSE)
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    ) if customer else []

    income_by_category = (
        transactions.filter(category__type=Category.INCOME)
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    ) if customer else []

    context = {
        "income_total": income_total,
        "expense_total": expense_total,
        "net_total": net_total,
        "transactions": transactions,
        "expense_by_category": expense_by_category,
        "income_by_category": income_by_category,
    }
    return render(request, "finance/dashboard.html", context)



@login_required
def add_transaction(request):
    customer = get_current_customer(request.user)
    if customer is None:
        # فعلاً ساده: بعداً می‌تونیم ریدایرکت کنیم به صفحه ساخت Customer
        return redirect("finance:dashboard")

    if request.method == "POST":
        form = TransactionForm(request.POST, customer=customer)
        if form.is_valid():
            transaction = form.save()
            return redirect("finance:dashboard")
    else:
        form = TransactionForm(customer=customer)

    return render(request, "finance/transaction_form.html", {"form": form})
