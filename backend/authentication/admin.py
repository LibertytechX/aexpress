from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for User model."""

    list_display = ['phone', 'business_name', 'contact_name', 'email', 'is_active', 'email_verified', 'created_at']
    list_filter = ['is_active', 'is_staff', 'email_verified', 'phone_verified', 'created_at']
    search_fields = ['phone', 'email', 'business_name', 'contact_name']
    ordering = ['-created_at']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Admin configuration for Address model."""

    list_display = ['user', 'label', 'address_preview', 'is_default', 'created_at']
    list_filter = ['is_default', 'created_at']
    search_fields = ['user__business_name', 'user__phone', 'label', 'address']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    def address_preview(self, obj):
        """Show preview of address."""
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
    address_preview.short_description = 'Address'

    fieldsets = (
        ('Business Information', {
            'fields': ('business_name', 'contact_name', 'phone', 'email', 'address')
        }),
        ('Verification Status', {
            'fields': ('email_verified', 'phone_verified')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )

    add_fieldsets = (
        ('Business Information', {
            'classes': ('wide',),
            'fields': ('business_name', 'contact_name', 'phone', 'email', 'password1', 'password2')
        }),
    )

    readonly_fields = ['created_at', 'updated_at', 'last_login']
