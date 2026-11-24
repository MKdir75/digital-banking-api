import pytest

from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

from .factories import UserFactory


User = get_user_model()


@pytest.mark.django_db
def test_customer_can_register():

    client = APIClient()

    response = client.post(
        "/api/auth/register/",
        {
            "username": "newcustomer",
            "email": "newcustomer@example.com",
            "phone_number": "01712345678",
            "password": "StrongPass!934",
            "password_confirm": "StrongPass!934",
        },
        format="json"
    )

    assert response.status_code == 201

    assert User.objects.filter(
        email="newcustomer@example.com"
    ).exists()

    user = User.objects.get(
        email="newcustomer@example.com"
    )

    assert user.check_password("StrongPass!934")


@pytest.mark.django_db
def test_customer_cannot_register_with_mismatched_passwords():

    client = APIClient()

    response = client.post(
        "/api/auth/register/",
        {
            "username": "invalidcustomer",
            "email": "invalid@example.com",
            "phone_number": "01712345678",
            "password": "StrongPass!934",
            "password_confirm": "DifferentPass!934",
        },
        format="json"
    )

    assert response.status_code == 400

    assert not User.objects.filter(
        email="invalid@example.com"
    ).exists()


@pytest.mark.django_db
def test_customer_can_obtain_jwt_tokens():

    user = UserFactory()

    client = APIClient()

    response = client.post(
        "/api/auth/token/",
        {
            "email": user.email,
            "password": "StrongPass!934",
        },
        format="json"
    )

    assert response.status_code == 200

    assert "access" in response.data

    assert "refresh" in response.data


@pytest.mark.django_db
def test_customer_can_refresh_access_token():

    user = UserFactory()

    client = APIClient()

    login_response = client.post(
        "/api/auth/token/",
        {
            "email": user.email,
            "password": "StrongPass!934",
        },
        format="json"
    )

    refresh_token = login_response.data["refresh"]

    response = client.post(
        "/api/auth/token/refresh/",
        {
            "refresh": refresh_token,
        },
        format="json"
    )

    assert response.status_code == 200

    assert "access" in response.data


@pytest.mark.django_db
def test_authenticated_customer_can_view_profile():

    user = UserFactory()

    client = APIClient()

    client.force_authenticate(user=user)

    response = client.get(
        "/api/auth/me/"
    )

    assert response.status_code == 200

    assert response.data["email"] == user.email

    assert response.data["username"] == user.username


@pytest.mark.django_db
def test_unauthenticated_customer_cannot_view_profile():

    client = APIClient()

    response = client.get(
        "/api/auth/me/"
    )

    assert response.status_code == 401
