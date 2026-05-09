from django.contrib import admin

from finance.models import Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "type")
    list_filter = ("type",)
    search_fields = ("name",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("date", "user", "type", "category", "amount", "is_mandatory")
    list_filter = ("type", "category", "is_mandatory")
    search_fields = ("source",)
    raw_id_fields = ("user",)
