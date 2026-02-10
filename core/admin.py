from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from . import models


@admin.register(models.User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'home_currency', 'is_staff', 'is_active')

    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('home_currency',)}),
    )

    add_fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('home_currency',)}),
    )
