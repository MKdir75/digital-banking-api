from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    password_confirm = serializers.CharField(
        write_only=True
    )


    class Meta:

        model = User

        fields = [
            "id",
            "username",
            "email",
            "phone_number",
            "password",
            "password_confirm",
        ]

        read_only_fields = ["id"]


    def validate(self, attrs):

        if attrs["password"] != attrs["password_confirm"]:

            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })

        attrs.pop("password_confirm")

        return attrs


    def create(self, validated_data):

        user = User.objects.create_user(
            **validated_data
        )

        return user


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:

        model = User

        fields = [
            "id",
            "username",
            "email",
            "phone_number",
            "role",
        ]

        read_only_fields = fields
