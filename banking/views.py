from django.db.models import Q

from rest_framework import (
    generics,
    permissions,
    status,
)

from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BankAccount, Transfer

from .serializers import (
    BankAccountSerializer,
    CreateAccountSerializer,
    TransferCreateSerializer,
    TransferSerializer,
    DepositCreateSerializer,
    DepositSerializer,
)

from .services import (
    transfer_funds,
    deposit_funds,
)


class AccountListCreateView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request):

        accounts = BankAccount.objects.filter(
            owner=request.user
        ).order_by("-created_at")

        serializer = BankAccountSerializer(
            accounts,
            many=True
        )

        return Response(serializer.data)

    def post(self, request):

        serializer = CreateAccountSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        account = BankAccount.objects.create(
            owner=request.user,
            currency=serializer.validated_data["currency"]
        )

        return Response(
            BankAccountSerializer(account).data,
            status=status.HTTP_201_CREATED
        )


class TransferCreateView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request):

        serializer = TransferCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        transfer = transfer_funds(
            actor=request.user,
            sender_id=data["sender_account_id"],
            receiver_account_number=data[
                "receiver_account_number"
            ],
            amount=data["amount"],
            idempotency_key=data["idempotency_key"],
            reference=data.get("reference", ""),
        )

        return Response(
            TransferSerializer(transfer).data,
            status=status.HTTP_200_OK
        )


class DepositCreateView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request):

        serializer = DepositCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        deposit = deposit_funds(
            actor=request.user,
            account_id=data["account_id"],
            amount=data["amount"],
            idempotency_key=data["idempotency_key"],
            reference=data.get("reference", ""),
        )

        return Response(
            DepositSerializer(deposit).data,
            status=status.HTTP_201_CREATED
        )


class TransferHistoryView(generics.ListAPIView):

    serializer_class = TransferSerializer

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):

        return Transfer.objects.filter(
            Q(sender__owner=self.request.user)
            |
            Q(receiver__owner=self.request.user)
        ).select_related(
            "sender",
            "receiver"
        ).distinct().order_by("-created_at")
