
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        (
            "Banking Information",
            {
                "fields": (
                    "role",
                    "phone_number",
                )
            }
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Banking Information",
            {
                "fields": (
                    "email",
                    "role",
                    "phone_number",
                )
            }
        ),
    )

    list_display = (
        "username",
        "email",
        "role",
        "is_active",
        "is_staff",
    )

    search_fields = (
        "email",
        "username",
    )
