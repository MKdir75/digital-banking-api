import factory

from django.contrib.auth import get_user_model

from banking.models import BankAccount


User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(
        lambda n: f"user{n}"
    )

    email = factory.Sequence(
        lambda n: f"user{n}@example.com"
    )

    password = factory.PostGenerationMethodCall(
        "set_password",
        "StrongPass!934"
    )


class BankAccountFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = BankAccount

    owner = factory.SubFactory(UserFactory)

    currency = "BDT"

    balance = "1000.00"
