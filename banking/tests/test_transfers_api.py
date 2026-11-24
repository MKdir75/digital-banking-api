
import pytest

from decimal import Decimal

from rest_framework.test import APIClient

from banking.models import (
    BankAccount,
    Transfer,
    LedgerEntry,
    AuditLog,
)

from .factories import UserFactory


@pytest.mark.django_db
def test_customer_can_transfer_money_through_api():

    sender_user = UserFactory()
    receiver_user = UserFactory()

    sender = BankAccount.objects.create(
        owner=sender_user,
        currency="BDT",
        balance=Decimal("1000.00")
    )

    receiver = BankAccount.objects.create(
        owner=receiver_user,
        currency="BDT",
        balance=Decimal("500.00")
    )

    client = APIClient()
    client.force_authenticate(user=sender_user)

    response = client.post(
        "/api/banking/transfers/",
        {
            "sender_account_id": str(sender.id),
            "receiver_account_number": receiver.account_number,
            "amount": "200.00",
            "idempotency_key": "api-transfer-001",
            "reference": "Test transfer"
        },
        format="json"
    )

    assert response.status_code == 200

    assert response.data["amount"] == "200.00"

    assert response.data["sender_account_number"] == sender.account_number

    assert response.data["receiver_account_number"] == receiver.account_number

    sender.refresh_from_db()
    receiver.refresh_from_db()

    assert sender.balance == Decimal("800.00")
    assert receiver.balance == Decimal("700.00")

    assert Transfer.objects.count() == 1

    assert LedgerEntry.objects.filter(
        transfer__isnull=False
    ).count() == 2

    assert AuditLog.objects.filter(
        action="TRANSFER_COMPLETED"
    ).exists()


@pytest.mark.django_db
def test_customer_can_see_own_transfer_history():

    user1 = UserFactory()
    user2 = UserFactory()
    user3 = UserFactory()

    sender = BankAccount.objects.create(
        owner=user1,
        currency="BDT",
        balance=Decimal("1000.00")
    )

    receiver = BankAccount.objects.create(
        owner=user2,
        currency="BDT",
        balance=Decimal("500.00")
    )

    unrelated_account = BankAccount.objects.create(
        owner=user3,
        currency="BDT",
        balance=Decimal("500.00")
    )

    Transfer.objects.create(
        sender=sender,
        receiver=receiver,
        amount=Decimal("100.00"),
        currency="BDT",
        idempotency_key="history-transfer-001",
        status="COMPLETED"
    )

    Transfer.objects.create(
        sender=unrelated_account,
        receiver=receiver,
        amount=Decimal("50.00"),
        currency="BDT",
        idempotency_key="history-transfer-002",
        status="COMPLETED"
    )

    client = APIClient()
    client.force_authenticate(user=user1)

    response = client.get(
        "/api/banking/transfers/history/"
    )

    assert response.status_code == 200

    assert response.data["count"] == 1

    assert len(response.data["results"]) == 1

    assert response.data["results"][0]["sender_account_number"] == sender.account_number

    assert response.data["results"][0]["receiver_account_number"] == receiver.account_number


@pytest.mark.django_db
def test_unauthenticated_user_cannot_create_transfer():

    client = APIClient()

    response = client.post(
        "/api/banking/transfers/",
        {},
        format="json"
    )

    assert response.status_code == 401
