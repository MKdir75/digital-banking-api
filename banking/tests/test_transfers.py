import pytest

from decimal import Decimal

from rest_framework.exceptions import ValidationError, NotFound

from banking.models import (
    BankAccount,
    Transfer,

)

from banking.services import transfer_funds

from .factories import UserFactory


@pytest.mark.django_db
def test_successful_transfer():

    sender_user = UserFactory()

    receiver_user = UserFactory()

    sender = BankAccount.objects.create(
        owner=sender_user,
        balance=Decimal("500.00")
    )

    receiver = BankAccount.objects.create(
        owner=receiver_user,
        balance=Decimal("100.00")
    )

    transfer = transfer_funds(

        actor=sender_user,

        sender_id=sender.pk,

        receiver_account_number=receiver.account_number,

        amount="125.00",

        idempotency_key="test-key-1",

    )

    sender.refresh_from_db()

    receiver.refresh_from_db()

    assert sender.balance == Decimal("375.00")

    assert receiver.balance == Decimal("225.00")

    assert transfer.ledger_entries.count() == 2

    assert transfer.ledger_entries.filter(
        entry_type="DEBIT"
    ).count() == 1

    assert transfer.ledger_entries.filter(
        entry_type="CREDIT"
    ).count() == 1


@pytest.mark.django_db
def test_insufficient_funds():

    sender_user = UserFactory()

    receiver_user = UserFactory()

    sender = BankAccount.objects.create(
        owner=sender_user,
        balance=Decimal("10.00")
    )

    receiver = BankAccount.objects.create(
        owner=receiver_user
    )

    with pytest.raises(ValidationError):

        transfer_funds(

            actor=sender_user,

            sender_id=sender.pk,

            receiver_account_number=receiver.account_number,

            amount="20.00",

            idempotency_key="insufficient-key",

        )


@pytest.mark.django_db
def test_idempotency_prevents_duplicate_transfer():

    sender_user = UserFactory()

    receiver_user = UserFactory()

    sender = BankAccount.objects.create(
        owner=sender_user,
        balance=Decimal("100.00")
    )

    receiver = BankAccount.objects.create(
        owner=receiver_user,
        balance=Decimal("0.00")
    )

    kwargs = {

        "actor": sender_user,

        "sender_id": sender.pk,

        "receiver_account_number": receiver.account_number,

        "amount": "10.00",

        "idempotency_key": "same-key",

    }

    first = transfer_funds(**kwargs)

    second = transfer_funds(**kwargs)

    sender.refresh_from_db()

    receiver.refresh_from_db()

    assert first.pk == second.pk

    assert sender.balance == Decimal("90.00")

    assert receiver.balance == Decimal("10.00")


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
def test_transfer_rejects_invalid_amount(amount):

    sender_user = UserFactory()

    receiver_user = UserFactory()

    sender = BankAccount.objects.create(
        owner=sender_user,
        balance=Decimal("500.00")
    )

    receiver = BankAccount.objects.create(
        owner=receiver_user,
        balance=Decimal("100.00")
    )

    with pytest.raises(ValidationError):

        transfer_funds(
            actor=sender_user,
            sender_id=sender.pk,
            receiver_account_number=receiver.account_number,
            amount=amount,
            idempotency_key="invalid-amount-key",
        )

    sender.refresh_from_db()
    receiver.refresh_from_db()

    assert sender.balance == Decimal("500.00")
    assert receiver.balance == Decimal("100.00")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "idempotency_key",
    [
        "",
        None,
        "a" * 101,
    ],
)
def test_transfer_rejects_invalid_idempotency_key(idempotency_key):

    sender_user = UserFactory()

    receiver_user = UserFactory()

    sender = BankAccount.objects.create(
        owner=sender_user,
        balance=Decimal("500.00")
    )

    receiver = BankAccount.objects.create(
        owner=receiver_user,
        balance=Decimal("100.00")
    )

    with pytest.raises(ValidationError):

        transfer_funds(
            actor=sender_user,
            sender_id=sender.pk,
            receiver_account_number=receiver.account_number,
            amount="50.00",
            idempotency_key=idempotency_key,
        )

    sender.refresh_from_db()
    receiver.refresh_from_db()

    assert sender.balance == Decimal("500.00")
    assert receiver.balance == Decimal("100.00")


@pytest.mark.django_db
def test_transfer_rejects_sender_account_owned_by_another_user():

    owner = UserFactory()
    attacker = UserFactory()
    receiver_user = UserFactory()

    sender = BankAccount.objects.create(
        owner=owner,
        balance=Decimal("500.00")
    )

    receiver = BankAccount.objects.create(
        owner=receiver_user,
        balance=Decimal("100.00")
    )

    with pytest.raises(NotFound):

        transfer_funds(
            actor=attacker,
            sender_id=sender.pk,
            receiver_account_number=receiver.account_number,
            amount="50.00",
            idempotency_key="ownership-test",
        )


@pytest.mark.django_db
def test_transfer_rejects_nonexistent_receiver():

    sender_user = UserFactory()

    sender = BankAccount.objects.create(
        owner=sender_user,
        balance=Decimal("500.00")
    )

    with pytest.raises(NotFound):

        transfer_funds(
            actor=sender_user,
            sender_id=sender.pk,
            receiver_account_number="DB0000000000000000",
            amount="50.00",
            idempotency_key="receiver-not-found",
        )

    sender.refresh_from_db()

    assert sender.balance == Decimal("500.00")


@pytest.mark.django_db
def test_transfer_rejects_frozen_sender_account():

    sender_user = UserFactory()
    receiver_user = UserFactory()

    sender = BankAccount.objects.create(
        owner=sender_user,
        balance=Decimal("500.00"),
        status=BankAccount.Status.FROZEN,
    )

    receiver = BankAccount.objects.create(
        owner=receiver_user,
        balance=Decimal("100.00"),
    )

    with pytest.raises(ValidationError):

        transfer_funds(
            actor=sender_user,
            sender_id=sender.pk,
            receiver_account_number=receiver.account_number,
            amount="50.00",
            idempotency_key="frozen-sender",
        )

    sender.refresh_from_db()
    receiver.refresh_from_db()

    assert sender.balance == Decimal("500.00")
    assert receiver.balance == Decimal("100.00")


@pytest.mark.django_db
def test_transfer_rejects_frozen_receiver_account():

    sender_user = UserFactory()
    receiver_user = UserFactory()

    sender = BankAccount.objects.create(
        owner=sender_user,
        balance=Decimal("500.00"),
    )

    receiver = BankAccount.objects.create(
        owner=receiver_user,
        balance=Decimal("100.00"),
        status=BankAccount.Status.FROZEN,
    )

    with pytest.raises(ValidationError):

        transfer_funds(
            actor=sender_user,
            sender_id=sender.pk,
            receiver_account_number=receiver.account_number,
            amount="50.00",
            idempotency_key="frozen-receiver",
        )

    sender.refresh_from_db()
    receiver.refresh_from_db()

    assert sender.balance == Decimal("500.00")
    assert receiver.balance == Decimal("100.00")


@pytest.mark.django_db
def test_transfer_rejects_currency_mismatch():

    sender_user = UserFactory()
    receiver_user = UserFactory()

    sender = BankAccount.objects.create(
        owner=sender_user,
        balance=Decimal("500.00"),
        currency="BDT",
    )

    receiver = BankAccount.objects.create(
        owner=receiver_user,
        balance=Decimal("100.00"),
        currency="USD",
    )

    with pytest.raises(ValidationError):

        transfer_funds(
            actor=sender_user,
            sender_id=sender.pk,
            receiver_account_number=receiver.account_number,
            amount="50.00",
            idempotency_key="currency-mismatch",
        )

    sender.refresh_from_db()
    receiver.refresh_from_db()

    assert sender.balance == Decimal("500.00")
    assert receiver.balance == Decimal("100.00")


@pytest.mark.django_db
def test_transfer_rejects_closed_sender_account():

    sender_user = UserFactory()
    receiver_user = UserFactory()

    sender = BankAccount.objects.create(
        owner=sender_user,
        balance=Decimal("500.00"),
        status=BankAccount.Status.CLOSED,
    )

    receiver = BankAccount.objects.create(
        owner=receiver_user,
        balance=Decimal("100.00"),
    )

    with pytest.raises(ValidationError):

        transfer_funds(
            actor=sender_user,
            sender_id=sender.pk,
            receiver_account_number=receiver.account_number,
            amount="50.00",
            idempotency_key="closed-sender",
        )

    sender.refresh_from_db()
    receiver.refresh_from_db()

    assert sender.balance == Decimal("500.00")
    assert receiver.balance == Decimal("100.00")


@pytest.mark.django_db
def test_transfer_rejects_same_idempotency_key_with_different_amount():

    sender_user = UserFactory()
    receiver_user = UserFactory()

    sender = BankAccount.objects.create(
        owner=sender_user,
        balance=Decimal("500.00"),
    )

    receiver = BankAccount.objects.create(
        owner=receiver_user,
        balance=Decimal("100.00"),
    )

    transfer_funds(
        actor=sender_user,
        sender_id=sender.pk,
        receiver_account_number=receiver.account_number,
        amount="50.00",
        idempotency_key="conflicting-key",
    )

    with pytest.raises(ValidationError):

        transfer_funds(
            actor=sender_user,
            sender_id=sender.pk,
            receiver_account_number=receiver.account_number,
            amount="75.00",
            idempotency_key="conflicting-key",
        )

    sender.refresh_from_db()
    receiver.refresh_from_db()

    assert sender.balance == Decimal("450.00")
    assert receiver.balance == Decimal("150.00")
    assert Transfer.objects.filter(
        sender=sender,
        idempotency_key="conflicting-key"
    ).count() == 1
