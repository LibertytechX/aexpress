"""
Referral service — handles commission crediting when a referred merchant's order completes.
"""

from decimal import Decimal
from django.utils import timezone


COMMISSION_RATE = Decimal("0.05")  # 5%


def fire_referral_commission(order):
    """
    Called after an order is marked Done.
    If the order's user (merchant) was referred by a rider, credit 5% to that rider's wallet.
    """
    from .models import RiderReferral, ReferralEarning

    try:
        referral = RiderReferral.objects.select_related("referring_rider__user").get(
            merchant=order.user, status=RiderReferral.Status.ACTIVE
        )
    except RiderReferral.DoesNotExist:
        # Check if it's still pending — activate and credit
        try:
            referral = RiderReferral.objects.select_related(
                "referring_rider__user"
            ).get(merchant=order.user, status=RiderReferral.Status.PENDING)
            referral.status = RiderReferral.Status.ACTIVE
            referral.activated_at = timezone.now()
            referral.save()
        except RiderReferral.DoesNotExist:
            return  # Not a referred merchant

    # Avoid double-crediting the same order
    if ReferralEarning.objects.filter(order=order).exists():
        return

    commission = (Decimal(str(order.total_amount)) * COMMISSION_RATE).quantize(
        Decimal("0.01")
    )

    if commission <= 0:
        return

    # Credit rider's wallet
    rider = referral.referring_rider
    try:
        from wallet.models import Wallet

        # Riders share the same auth user structure — look up by rider.user
        wallet = Wallet.objects.get(user=rider.user)
        wallet.credit(
            amount=commission,
            description=f"Referral commission — Order {order.order_number}",
            reference=f"REF-{order.order_number}",
            metadata={
                "type": "referral_commission",
                "order_id": str(order.id),
                "merchant": order.user.business_name,
                "rate": "5%",
            },
        )
    except Exception:
        # Don't crash the order flow if wallet credit fails — log and continue
        import traceback

        traceback.print_exc()
        return

    # Record the earning
    ReferralEarning.objects.create(
        referral=referral,
        order=order,
        commission_amount=commission,
    )
