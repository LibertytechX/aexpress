# Generated manually for V2 verification codes
from django.db import migrations, models
import secrets


def populate_verification_codes(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    Delivery = apps.get_model("orders", "Delivery")

    # Backfill Order pickup codes
    for order in Order.objects.filter(pickup_code__isnull=True).iterator():
        order.pickup_code = f"{secrets.randbelow(900000) + 100000}"
        order.save(update_fields=["pickup_code"])

    # Backfill Delivery drop codes
    for delivery in Delivery.objects.filter(drop_code__isnull=True).iterator():
        delivery.drop_code = f"{secrets.randbelow(900000) + 100000}"
        delivery.save(update_fields=["drop_code"])


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0016_googleplace_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="pickup_code",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="6-digit verification code used by rider to confirm package pickup",
                max_length=6,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="pickup_code_attempts",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="Consecutive failed pickup code attempts (locks at 5)",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="pickup_verified_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Timestamp when pickup code was successfully verified",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="delivery",
            name="drop_code",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="6-digit verification code used by rider to confirm package delivery",
                max_length=6,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="delivery",
            name="drop_code_attempts",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="Consecutive failed drop code attempts (locks at 5)",
            ),
        ),
        migrations.AddField(
            model_name="delivery",
            name="drop_verified_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Timestamp when drop code was successfully verified",
                null=True,
            ),
        ),
        migrations.RunPython(populate_verification_codes, migrations.RunPython.noop),
    ]

