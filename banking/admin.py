
from django.contrib import admin

from .models import (
    BankAccount,
    Transfer,
    LedgerEntry,
    AuditLog,
)


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):

    list_display = (
        "account_number",
        "owner",
        "balance",
        "currency",
        "status",
        "created_at",
    )

    search_fields = (
        "account_number",
        "owner__email",
    )

    readonly_fields = (
        "id",
        "account_number",
        "balance",
        "created_at",
    )


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "sender",
        "receiver",
        "amount",
        "currency",
        "status",
        "created_at",
    )

    readonly_fields = [
        field.name
        for field in Transfer._meta.fields
    ]


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):

    list_display = (
        "transfer",
        "account",
        "entry_type",
        "amount",
        "created_at",
    )

    readonly_fields = [
        field.name
        for field in LedgerEntry._meta.fields
    ]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    list_display = (
        "actor",
        "action",
        "object_type",
        "object_id",
        "created_at",
    )

    readonly_fields = [
        field.name
        for field in AuditLog._meta.fields
    ]
