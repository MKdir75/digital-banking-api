
import pytest

from decimal import Decimal

from rest_framework.test import APIClient

from banking.models import (
    BankAccount,
    Deposit,
    LedgerEntry,
    AuditLog,
)

from .factories import UserFactory


@pytest.mark.django_db
def test_customer_can_deposit_money_through_api():

    user = UserFactory()

    account = BankAccount.objects.create(
        owner=user,
        currency="BDT",
        balance=Decimal("500.00")
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        "/api/banking/deposits/",
        {
            "account_id": str(account.id),
            "amount": "200.00",
            "idempotency_key": "api-deposit-001",
            "reference": "Test deposit"
        },
        format="json"
    )

    assert response.status_code == 201

    assert response.data["amount"] == "200.00"

    assert response.data["account_number"] == account.account_number

    account.refresh_from_db()

    assert account.balance == Decimal("700.00")

    assert Deposit.objects.count() == 1

    assert LedgerEntry.objects.filter(
        deposit__isnull=False
    ).count() == 1

    assert AuditLog.objects.filter(
        action="DEPOSIT_COMPLETED"
    ).exists()


@pytest.mark.django_db
def test_customer_cannot_deposit_into_another_users_account():

    owner = UserFactory()
    attacker = UserFactory()

    account = BankAccount.objects.create(
        owner=owner,
        currency="BDT",
        balance=Decimal("500.00")
    )

    client = APIClient()
    client.force_authenticate(user=attacker)

    response = client.post(
        "/api/banking/deposits/",
        {
            "account_id": str(account.id),
            "amount": "200.00",
            "idempotency_key": "unauthorized-deposit-001",
            "reference": "Unauthorized deposit"
        },
        format="json"
    )

    assert response.status_code == 404

    account.refresh_from_db()

    assert account.balance == Decimal("500.00")

    assert Deposit.objects.count() == 0


@pytest.mark.django_db
def test_unauthenticated_user_cannot_create_deposit():

    client = APIClient()

    response = client.post(
        "/api/banking/deposits/",
        {},
        format="json"
    )

    assert response.status_code == 401
