from enum import Enum


class EnumBaseClass:

    @classmethod
    def choices(cls):
        return [(x.value, x.name) for x in cls]

    @classmethod
    def values(cls):
        return [x.value for x in cls]


class WebhookEventEnum(EnumBaseClass, Enum):
    ORDER_CREATED = "order-created"
    ORDER_ASSIGNED = "order-assigned"
    ORDER_DELIVERED = "order-delivered"
    ORDER_CANCELLED = "order-cancelled"
    ORDER_UPDATED = "order-updated"
    ORDER_COMPLETED = "order-completed"
