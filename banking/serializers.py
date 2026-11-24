from rest_framework import serializers
from decimal import Decimal
from .models import BankAccount, Transfer, Deposit 


class BankAccountSerializer(serializers.ModelSerializer):

    class Meta:

        model = BankAccount

        fields = [
            "id",
            "account_number",
            "currency",
            "balance",
            "status",
            "created_at",
        ]

        read_only_fields = fields


class CreateAccountSerializer(serializers.Serializer):

    currency = serializers.ChoiceField(
        choices=["BDT", "USD", "EUR"],
        default="BDT"
    )


class TransferCreateSerializer(serializers.Serializer):

    sender_account_id = serializers.UUIDField()

    receiver_account_number = serializers.CharField(
        max_length=20
    )

    amount = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        min_value=Decimal("0.01")
    )

    idempotency_key = serializers.CharField(
        max_length=100
    )

    reference = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True
    )


class TransferSerializer(serializers.ModelSerializer):

    sender_account_number = serializers.CharField(
        source="sender.account_number",
        read_only=True
    )

    receiver_account_number = serializers.CharField(
        source="receiver.account_number",
        read_only=True
    )

    class Meta:

        model = Transfer

        fields = [
            "id",
            "sender_account_number",
            "receiver_account_number",
            "amount",
            "currency",
            "reference",
            "status",
            "created_at",
        ]

        read_only_fields = fields

class DepositCreateSerializer(serializers.Serializer):

    account_id = serializers.UUIDField()

    amount = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        min_value=Decimal("0.01")
    )

    idempotency_key = serializers.CharField(
        max_length=100
    )

    reference = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True
    )


class DepositSerializer(serializers.ModelSerializer):

    account_number = serializers.CharField(
        source="account.account_number",
        read_only=True
    )

    class Meta:

        model = Deposit

        fields = [
            "id",
            "account_number",
            "amount",
            "currency",
            "reference",
            "status",
            "created_at",
        ]

        read_only_fields = fields
