from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import F

from rest_framework.exceptions import (
    ValidationError,
    NotFound,
)

from .models import (
    BankAccount,
    Transfer,
    Deposit,
    LedgerEntry,
    AuditLog,
)


@transaction.atomic
def transfer_funds(
    *,
    actor,
    sender_id,
    receiver_account_number,
    amount,
    idempotency_key,
    reference=""
):

    # 1. Validate amount

    try:
        amount = Decimal(str(amount))

    except (InvalidOperation, ValueError):
        raise ValidationError({
            "amount": "Invalid amount."
        })

    if not amount.is_finite() or amount <= 0:

        raise ValidationError({
            "amount": "Amount must be positive."
        })

    if amount.as_tuple().exponent < -2:

        raise ValidationError({
            "amount": "Maximum two decimal places allowed."
        })


    # 2. Validate idempotency key

    if not idempotency_key or len(idempotency_key) > 100:

        raise ValidationError({
            "idempotency_key": "Valid idempotency key required."
        })


    # 3. Find sender account

    try:

        sender = BankAccount.objects.get(
            pk=sender_id,
            owner=actor
        )

    except BankAccount.DoesNotExist:

        raise NotFound("Sender account not found.")


    # 4. Find receiver account

    try:

        receiver = BankAccount.objects.get(
            account_number=receiver_account_number
        )

    except BankAccount.DoesNotExist:

        raise NotFound("Receiver account not found.")


    # 5. Prevent self transfer

    if sender.pk == receiver.pk:

        raise ValidationError(
            "Cannot transfer to the same account."
        )


    # 6. Lock both accounts in consistent order

    account_ids = sorted(
        [sender.pk, receiver.pk],
        key=str
    )

    locked_accounts = list(
        BankAccount.objects
        .select_for_update()
        .filter(pk__in=account_ids)
        .order_by("pk")
    )

    locked = {
        account.pk: account
        for account in locked_accounts
    }

    sender = locked[sender.pk]
    receiver = locked[receiver.pk]


    # 7. Check idempotency after obtaining lock

    existing = Transfer.objects.filter(
        sender=sender,
        idempotency_key=idempotency_key
    ).first()

    if existing:

        if (
            existing.receiver_id != receiver.pk
            or existing.amount != amount
            or existing.reference != reference
        ):

            raise ValidationError({
                "idempotency_key": "This key was already used for a different request."
            })

        return existing


    # 8. Account status validation

    if sender.status != BankAccount.Status.ACTIVE:

        raise ValidationError(
            "Sender account is not active."
        )

    if receiver.status != BankAccount.Status.ACTIVE:

        raise ValidationError(
            "Receiver account is not active."
        )


    # 9. Currency validation

    if sender.currency != receiver.currency:

        raise ValidationError(
            "Currency mismatch."
        )


    # 10. Check balance

    if sender.balance < amount:

        raise ValidationError({
            "amount": "Insufficient funds."
        })


    # 11. Update sender balance

    BankAccount.objects.filter(
        pk=sender.pk
    ).update(
        balance=F("balance") - amount
    )


    # 12. Update receiver balance

    BankAccount.objects.filter(
        pk=receiver.pk
    ).update(
        balance=F("balance") + amount
    )


    # 13. Create transfer record

    transfer = Transfer.objects.create(

        sender=sender,

        receiver=receiver,

        amount=amount,

        currency=sender.currency,

        reference=reference,

        idempotency_key=idempotency_key,

        status=Transfer.Status.COMPLETED,

    )


    # 14. Create double-entry ledger

    LedgerEntry.objects.bulk_create([

        LedgerEntry(
            transfer=transfer,
            account=sender,
            entry_type=LedgerEntry.EntryType.DEBIT,
            amount=amount
        ),

        LedgerEntry(
            transfer=transfer,
            account=receiver,
            entry_type=LedgerEntry.EntryType.CREDIT,
            amount=amount
        ),

    ])


    # 15. Create audit log

    AuditLog.objects.create(

        actor=actor,

        action="TRANSFER_COMPLETED",

        object_type="Transfer",

        object_id=str(transfer.pk),

        metadata={
            "amount": str(amount),
            "currency": sender.currency,
        }

    )


    return transfer

@transaction.atomic
def deposit_funds(
    *,
    actor,
    account_id,
    amount,
    idempotency_key,
    reference=""
):

    # 1. Validate amount

    try:
        amount = Decimal(str(amount))

    except (InvalidOperation, ValueError):
        raise ValidationError({
            "amount": "Invalid amount."
        })

    if not amount.is_finite() or amount <= 0:
        raise ValidationError({
            "amount": "Amount must be positive."
        })

    if amount.as_tuple().exponent < -2:
        raise ValidationError({
            "amount": "Maximum two decimal places allowed."
        })

    # 2. Validate idempotency key

    if not idempotency_key or len(idempotency_key) > 100:
        raise ValidationError({
            "idempotency_key": "Valid idempotency key required."
        })

    # 3. Find and lock account

    try:
        account = (
            BankAccount.objects
            .select_for_update()
            .get(
                pk=account_id,
                owner=actor
            )
        )

    except BankAccount.DoesNotExist:
        raise NotFound("Bank account not found.")

    # 4. Check existing deposit

    existing = Deposit.objects.filter(
        account=account,
        idempotency_key=idempotency_key
    ).first()

    if existing:

        if (
            existing.amount != amount
            or existing.reference != reference
        ):
            raise ValidationError({
                "idempotency_key":
                "This key was already used for a different request."
            })

        return existing

    # 5. Check account status

    if account.status != BankAccount.Status.ACTIVE:
        raise ValidationError(
            "Account is not active."
        )

    # 6. Create deposit record

    deposit = Deposit.objects.create(
        account=account,
        amount=amount,
        currency=account.currency,
        reference=reference,
        idempotency_key=idempotency_key,
        status=Deposit.Status.COMPLETED
    )

    # 7. Update account balance

    BankAccount.objects.filter(
        pk=account.pk
    ).update(
        balance=F("balance") + amount
    )

    # 8. Create CREDIT ledger entry

    LedgerEntry.objects.create(
        deposit=deposit,
        account=account,
        entry_type=LedgerEntry.EntryType.CREDIT,
        amount=amount
    )

    # 9. Create audit log

    AuditLog.objects.create(
        actor=actor,
        action="DEPOSIT_COMPLETED",
        object_type="Deposit",
        object_id=str(deposit.pk),
        metadata={
            "amount": str(amount),
            "currency": account.currency,
            "account_number": account.account_number
        }
    )

    return deposit
