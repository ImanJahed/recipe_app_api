from django.contrib import admin  # noqa
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from core.models import User, Recipe

# Register your models here.


class UserAdmin(BaseUserAdmin):
    """Define the admin page for user"""

    ordering = ["id"]
    list_display = ["email", "first_name", "last_name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name")}),
        ("Permission", {"fields": ("is_active", "is_staff", "is_superuser")}),
        (
            "Important Dates",
            {
                "fields": "last_login",
            },
        ),
    )
    readonly_fields = ["last_login"]
    add_fieldsets = (
        None,
        {
            "classes": ("wide",),
            "fields": (
                "email",
                "password1",
                "password2",
                "first_name",
                "last_name",
                "is_active",
                "is_staff",
                "is_superuser",
            ),
        },
    )


admin.site.register(User, UserAdmin)
admin.site.register(Recipe)
