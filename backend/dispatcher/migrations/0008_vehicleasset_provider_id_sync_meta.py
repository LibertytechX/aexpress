from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dispatcher", "0004_vehicleasset_rider_vehicle_asset"),
    ]

    operations = [
        migrations.AddField(
            model_name="vehicleasset",
            name="provider_id",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="Device ID from the Concept Nova tracking API (used for telemetry sync)",
                max_length=64,
                null=True,
                unique=True,
            ),
        ),
        migrations.AddField(
            model_name="vehicleasset",
            name="sync_meta",
            field=models.JSONField(
                blank=True,
                help_text="Last sync result: {response_code, response_snippet, synced_at}",
                null=True,
            ),
        ),
    ]

