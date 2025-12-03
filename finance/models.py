from django.db import models


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


class Account(TimeStampedModel):
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
        return self.name


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
