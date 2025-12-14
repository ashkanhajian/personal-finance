from django.db import models
from django.conf import settings
from django.db.models import Sum


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    INCOME = "income"
    EXPENSE = "expense"

    CATEGORY_TYPES = [
        (INCOME, "Income"),
        (EXPENSE, "Expense"),
    ]

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    color = models.CharField(
        max_length=7,
        blank=True,
        help_text="Optional hex color, e.g. #ff0000",
    )

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["type", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class Customer(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    full_name = models.CharField(max_length=150, blank=True)
    national_id = models.CharField(max_length=50, null=True, blank=True, unique=True)

    phone_number = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["full_name", "id"]

    def __str__(self):
        return self.full_name or self.user.username


class Account(TimeStampedModel):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="accounts",
    )
    name = models.CharField(max_length=100)
    initial_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Initial balance of this account",
    )
    currency = models.CharField(
        max_length=10,
        default="IRR",
        help_text="e.g. IRR, USD, EUR",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.currency})"


class Transaction(TimeStampedModel):
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.date} - {self.amount} ({self.category})"

    @property
    def is_income(self):
        return self.category.type == Category.INCOME

    @property
    def is_expense(self):
        return self.category.type == Category.EXPENSE

class LedgerAccount(TimeStampedModel):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    INCOME = "income"
    EXPENSE = "expense"

    TYPES = [
        (ASSET, "Asset"),
        (LIABILITY, "Liability"),
        (EQUITY, "Equity"),
        (INCOME, "Income"),
        (EXPENSE, "Expense"),
    ]

    customer = models.ForeignKey("Customer", on_delete=models.CASCADE, related_name="ledger_accounts")
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=12, choices=TYPES)

    # برای لینک دادن به Account فعلی (اختیاری ولی کاربردی)
    bank_account = models.OneToOneField(
        "Account",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ledger_account",
    )

    def balance(self):
        totals = self.lines.aggregate(
            debit_sum=Sum("debit"),
            credit_sum=Sum("credit"),
        )
        debit = totals["debit_sum"] or 0
        credit = totals["credit_sum"] or 0

        if self.type in [self.ASSET, self.EXPENSE]:
            return debit - credit
        return credit - debit
    class Meta:
        unique_together = [("customer", "name")]
        ordering = ["type", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class JournalEntry(TimeStampedModel):
    customer = models.ForeignKey("Customer", on_delete=models.CASCADE, related_name="journal_entries")
    date = models.DateField()
    memo = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"JE#{self.id} {self.date} {self.memo}"


class LedgerLine(TimeStampedModel):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="lines")
    account = models.ForeignKey(LedgerAccount, on_delete=models.PROTECT, related_name="lines")

    # فقط یکی از این‌ها باید پر باشد
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.account} D:{self.debit} C:{self.credit}"

class Transfer(TimeStampedModel):
    customer = models.ForeignKey("Customer", on_delete=models.CASCADE, related_name="transfers")
    from_account = models.ForeignKey(
        "Account", on_delete=models.PROTECT, related_name="outgoing_transfers"
    )
    to_account = models.ForeignKey(
        "Account", on_delete=models.PROTECT, related_name="incoming_transfers"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    memo = models.CharField(max_length=255, blank=True)

    journal_entry = models.OneToOneField(
        "JournalEntry", on_delete=models.PROTECT, null=True, blank=True
    )

    def __str__(self):
        return f"{self.from_account} → {self.to_account} ({self.amount})"