import factory

from django.contrib.auth import get_user_model


User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = User

    username = factory.Sequence(
        lambda n: f"authuser{n}"
    )

    email = factory.Sequence(
        lambda n: f"authuser{n}@example.com"
    )

    phone_number = "01712345678"

    password = factory.django.Password(
        "StrongPass!934"
    )