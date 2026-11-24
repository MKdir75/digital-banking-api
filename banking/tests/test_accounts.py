import pytest

from rest_framework.test import APIClient

from banking.models import BankAccount

from .factories import UserFactory


@pytest.mark.django_db
def test_customer_can_create_account():

    user = UserFactory()

    client = APIClient()

    client.force_authenticate(user=user)

    response = client.post(
        "/api/banking/accounts/",
        {
            "currency": "BDT"
        },
        format="json"
    )

    assert response.status_code == 201

    assert response.data["currency"] == "BDT"

    assert BankAccount.objects.filter(
        owner=user
    ).exists()


@pytest.mark.django_db
def test_customer_sees_only_own_accounts():

    user1 = UserFactory()

    user2 = UserFactory()

    BankAccount.objects.create(
        owner=user1
    )

    BankAccount.objects.create(
        owner=user2
    )

    client = APIClient()

    client.force_authenticate(user=user1)

    response = client.get(
        "/api/banking/accounts/"
    )

    assert response.status_code == 200

    assert len(response.data) == 1
