from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render, redirect

from .form import TransferForm, TransactionForm
from .models import Account, Category, Transaction
from finance.services.exceptions import InsufficientFundsError
from finance.services.inter_customer_transfers import transfer_to_national_id
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


@login_required
def new_transfer(request):
    customer = get_current_customer(request.user)
    if customer is None:
        messages.error(request, "Customer profile not found.")
        return redirect("finance:dashboard")

    accounts_qs = Account.objects.filter(customer=customer, is_active=True).order_by("name")

    if request.method == "POST":
        form = TransferForm(request.POST, accounts_qs=accounts_qs)
        if form.is_valid():
            from_account = form.cleaned_data["from_account"]
            recipient_national_id = form.cleaned_data["recipient_national_id"]
            amount = form.cleaned_data["amount"]
            date = form.cleaned_data["date"]
            memo = form.cleaned_data["memo"]

            try:
                transfer_to_national_id(
                    sender=customer,
                    from_account=from_account,
                    recipient_national_id=recipient_national_id,
                    amount=amount,
                    date=date,
                    memo=memo,
                )
                messages.success(request, "Transfer completed successfully.")
                return redirect("finance:dashboard")
            except InsufficientFundsError:
                messages.error(request, "Insufficient funds.")
            except ValueError:

                messages.error(request, "Transfer failed. Check recipient and inputs.")
    else:
        form = TransferForm(accounts_qs=accounts_qs)

    return render(request, "finance/transfer_form.html", {"form": form})
