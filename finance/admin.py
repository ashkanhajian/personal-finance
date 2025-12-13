from django.contrib import admin

from django.contrib import admin
from .models import Category, Account, Transaction, Customer

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "color", "created_at")
    list_filter = ("type",)
    search_fields = ("name",)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "initial_balance", "currency", "is_active")
    list_filter = ("is_active", "currency")
    search_fields = ("name",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("date", "amount", "category", "account", "created_at")
    list_filter = ("category", "account", "date")
    search_fields = ("description",)
    date_hierarchy = "date"

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "phone_number", "national_id")
    search_fields = ("full_name", "user__username", "phone_number", "national_id")
