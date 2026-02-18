# Generated manually for password reset feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_add_email_verification_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='password_reset_token',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='user',
            name='password_reset_token_created',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

