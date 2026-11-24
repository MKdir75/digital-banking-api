import pytest

from decimal import Decimal

from rest_framework.exceptions import ValidationError

from banking.models import (
    BankAccount,
    Deposit,
    LedgerEntry,
    AuditLog,
)

from banking.services import deposit_funds

from .factories import UserFactory


@pytest.mark.django_db
def test_successful_deposit():

    user = UserFactory()

    account = BankAccount.objects.create(
        owner=user,
        balance=Decimal("500.00"),
    )

    deposit = deposit_funds(
        actor=user,
        account_id=account.pk,
        amount="200.00",
        idempotency_key="deposit-001",
    )

    account.refresh_from_db()

    assert account.balance == Decimal("700.00")

    assert Deposit.objects.filter(
        pk=deposit.pk
    ).exists()

    assert LedgerEntry.objects.filter(
        deposit=deposit,
        account=account,
        entry_type=LedgerEntry.EntryType.CREDIT,
        amount=Decimal("200.00"),
    ).count() == 1

    assert AuditLog.objects.filter(
        actor=user,
        action="DEPOSIT_COMPLETED",
    ).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "amount",
    [
        "0",
        "-10.00",
        "invalid",
        "10.999",
    ],
)
def test_deposit_rejects_invalid_amount(amount):

    user = UserFactory()

    account = BankAccount.objects.create(
        owner=user,
        balance=Decimal("500.00"),
    )

    with pytest.raises(ValidationError):

        deposit_funds(
            actor=user,
            account_id=account.pk,
            amount=amount,
            idempotency_key="invalid-deposit",
        )

    account.refresh_from_db()

    assert account.balance == Decimal("500.00")
    assert Deposit.objects.count() == 0


@pytest.mark.django_db
def test_deposit_idempotency_prevents_duplicate_deposit():

    user = UserFactory()

    account = BankAccount.objects.create(
        owner=user,
        balance=Decimal("500.00"),
    )

    first_deposit = deposit_funds(
        actor=user,
        account_id=account.pk,
        amount="200.00",
        idempotency_key="duplicate-deposit",
    )

    second_deposit = deposit_funds(
        actor=user,
        account_id=account.pk,
        amount="200.00",
        idempotency_key="duplicate-deposit",
    )

    account.refresh_from_db()

    assert account.balance == Decimal("700.00")

    assert first_deposit.pk == second_deposit.pk

    assert Deposit.objects.filter(
        account=account,
        idempotency_key="duplicate-deposit",
    ).count() == 1

@pytest.mark.django_db
def test_deposit_rejects_same_idempotency_key_with_different_amount():

    user = UserFactory()

    account = BankAccount.objects.create(
        owner=user,
        balance=Decimal("500.00"),
    )

    deposit_funds(
        actor=user,
        account_id=account.pk,
        amount="200.00",
        idempotency_key="conflicting-deposit",
    )

    with pytest.raises(ValidationError):

        deposit_funds(
            actor=user,
            account_id=account.pk,
            amount="300.00",
            idempotency_key="conflicting-deposit",
        )

    account.refresh_from_db()

    assert account.balance == Decimal("700.00")

    assert Deposit.objects.filter(
        account=account,
        idempotency_key="conflicting-deposit",
    ).count() == 1

from rest_framework.exceptions import NotFound


@pytest.mark.django_db
def test_deposit_rejects_account_owned_by_another_user():

    owner = UserFactory()
    attacker = UserFactory()

    account = BankAccount.objects.create(
        owner=owner,
        balance=Decimal("500.00"),
    )

    with pytest.raises(NotFound):

        deposit_funds(
            actor=attacker,
            account_id=account.pk,
            amount="100.00",
            idempotency_key="unauthorized-deposit",
        )

    account.refresh_from_db()

    assert account.balance == Decimal("500.00")
    assert Deposit.objects.count() == 0


@pytest.mark.django_db
def test_deposit_rejects_nonexistent_account():

    user = UserFactory()

    with pytest.raises(NotFound):

        deposit_funds(
            actor=user,
            account_id="00000000-0000-0000-0000-000000000000",
            amount="100.00",
            idempotency_key="missing-account",
        )

    assert Deposit.objects.count() == 0

@pytest.mark.django_db
@pytest.mark.parametrize(
    "status",
    [
        BankAccount.Status.FROZEN,
        BankAccount.Status.CLOSED,
    ],
)
def test_deposit_rejects_inactive_account(status):

    user = UserFactory()

    account = BankAccount.objects.create(
        owner=user,
        balance=Decimal("500.00"),
        status=status,
    )

    with pytest.raises(ValidationError):

        deposit_funds(
            actor=user,
            account_id=account.pk,
            amount="100.00",
            idempotency_key="inactive-deposit",
        )

    account.refresh_from_db()

    assert account.balance == Decimal("500.00")
    assert Deposit.objects.count() == 0

@pytest.mark.django_db
def test_deposit_rejects_same_key_with_different_reference():

    user = UserFactory()

    account = BankAccount.objects.create(
        owner=user,
        balance=Decimal("500.00"),
    )

    deposit_funds(
        actor=user,
        account_id=account.pk,
        amount="200.00",
        idempotency_key="reference-conflict",
        reference="First deposit",
    )

    with pytest.raises(ValidationError):

        deposit_funds(
            actor=user,
            account_id=account.pk,
            amount="200.00",
            idempotency_key="reference-conflict",
            reference="Second deposit",
        )

    account.refresh_from_db()

    assert account.balance == Decimal("700.00")

    assert Deposit.objects.filter(
        account=account,
        idempotency_key="reference-conflict",
    ).count() == 1
