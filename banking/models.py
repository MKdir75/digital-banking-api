import uuid

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q


class BankAccount(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        FROZEN = "FROZEN", "Frozen"
        CLOSED = "CLOSED", "Closed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bank_accounts"
    )

    account_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )

    currency = models.CharField(
        max_length=3,
        default="BDT"
    )

    balance = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00")
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        if not self.account_number:

            self.account_number = (
                "DB" + uuid.uuid4().hex[:16].upper()
            )

        super().save(*args, **kwargs)

    def __str__(self):

        return self.account_number


class Transfer(models.Model):

    class Status(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    sender = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name="sent_transfers"
    )

    receiver = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name="received_transfers"
    )

    amount = models.DecimalField(
        max_digits=18,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=3
    )

    reference = models.CharField(
        max_length=100,
        blank=True
    )

    idempotency_key = models.CharField(
        max_length=100
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.COMPLETED
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = ["-created_at"]

        constraints = [

            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="transfer_amount_positive"
            ),

            models.UniqueConstraint(
                fields=["sender", "idempotency_key"],
                name="unique_sender_idempotency"
            ),

        ]


class Deposit(models.Model):

    class Status(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name="deposits"
    )

    amount = models.DecimalField(
        max_digits=18,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=3
    )

    reference = models.CharField(
        max_length=100,
        blank=True
    )

    idempotency_key = models.CharField(
        max_length=100
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.COMPLETED
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = ["-created_at"]

        constraints = [

            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="deposit_amount_positive"
            ),

            models.UniqueConstraint(
                fields=["account", "idempotency_key"],
                name="unique_account_deposit_idempotency"
            ),

        ]


class LedgerEntry(models.Model):

    class EntryType(models.TextChoices):
        DEBIT = "DEBIT", "Debit"
        CREDIT = "CREDIT", "Credit"

    transfer = models.ForeignKey(
        Transfer,
        on_delete=models.PROTECT,
        related_name="ledger_entries",
        null=True,
        blank=True
    )

    deposit = models.ForeignKey(
        Deposit,
        on_delete=models.PROTECT,
        related_name="ledger_entries",
        null=True,
        blank=True
    )

    account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name="ledger_entries"
    )

    entry_type = models.CharField(
        max_length=6,
        choices=EntryType.choices
    )

    amount = models.DecimalField(
        max_digits=18,
        decimal_places=2
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        constraints = [

            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="ledger_amount_positive"
            ),

            models.CheckConstraint(
                condition=(
                    Q(
                        transfer__isnull=False,
                        deposit__isnull=True
                    )
                    |
                    Q(
                        transfer__isnull=True,
                        deposit__isnull=False
                    )
                ),
                name="ledger_exactly_one_transaction"
            ),

        ]


class AuditLog(models.Model):

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    action = models.CharField(
        max_length=80
    )

    object_type = models.CharField(
        max_length=80
    )

    object_id = models.CharField(
        max_length=80
    )

    metadata = models.JSONField(
        default=dict,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = ["-created_at"]
