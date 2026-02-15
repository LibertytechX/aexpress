from django.contrib import admin
from .models import Vehicle, Order, Delivery


class DeliveryInline(admin.TabularInline):
    """Inline admin for deliveries within an order."""
    model = Delivery
    extra = 0
    fields = ['sequence', 'dropoff_address', 'receiver_name', 'receiver_phone', 'package_type', 'status']
    readonly_fields = ['sequence']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """Admin configuration for Vehicle model."""

    list_display = ['name', 'max_weight_kg', 'base_price', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    ordering = ['base_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin configuration for Order model."""

    list_display = ['order_number', 'user', 'mode', 'vehicle', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'mode', 'payment_method', 'created_at']
    search_fields = ['order_number', 'user__business_name', 'user__phone', 'pickup_address']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'mode', 'status')
        }),
        ('Pickup Details', {
            'fields': ('pickup_address', 'sender_name', 'sender_phone')
        }),
        ('Delivery Details', {
            'fields': ('vehicle', 'payment_method', 'total_amount')
        }),
        ('Additional Information', {
            'fields': ('notes', 'scheduled_pickup_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    inlines = [DeliveryInline]


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    """Admin configuration for Delivery model."""

    list_display = ['order', 'sequence', 'receiver_name', 'dropoff_address', 'status', 'created_at']
    list_filter = ['status', 'package_type', 'created_at']
    search_fields = ['order__order_number', 'receiver_name', 'receiver_phone', 'dropoff_address']
    readonly_fields = ['created_at', 'delivered_at']
    ordering = ['order', 'sequence']

    fieldsets = (
        ('Order Information', {
            'fields': ('order', 'sequence', 'status')
        }),
        ('Dropoff Details', {
            'fields': ('dropoff_address', 'receiver_name', 'receiver_phone')
        }),
        ('Package Information', {
            'fields': ('package_type', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'delivered_at')
        }),
    )
