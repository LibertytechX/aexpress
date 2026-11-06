import hashlib
import secrets
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from dispatcher.models import ServiceAPIKey


class Command(BaseCommand):
    help = "Generate a service API key for inter-project auth (e.g. OCC → Main Backend)"

    def add_arguments(self, parser):
        parser.add_argument("name", type=str, help='Key name, e.g. "OCC Production"')
        parser.add_argument(
            "--scopes",
            nargs="+",
            default=["occ:read"],
            help='Scopes to grant, e.g. occ:read occ:write',
        )
        parser.add_argument(
            "--expires-days",
            type=int,
            default=365,
            help="Number of days until the key expires (default: 365)",
        )

    def handle(self, *args, **options):
        raw_key = "sk_" + secrets.token_urlsafe(48)
        prefix = raw_key[:11]  # "sk_" + first 8 chars of the token
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        ServiceAPIKey.objects.create(
            name=options["name"],
            prefix=prefix,
            key_hash=key_hash,
            scopes=options["scopes"],
            expires_at=timezone.now() + timedelta(days=options["expires_days"]),
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'=' * 60}\n"
                f"  Service API Key Created\n"
                f"{'=' * 60}\n"
                f"  Name:    {options['name']}\n"
                f"  Scopes:  {options['scopes']}\n"
                f"  Expires: {options['expires_days']} days\n"
                f"{'=' * 60}\n"
                f"\n  KEY (store securely — shown ONCE):\n\n"
                f"  {raw_key}\n\n"
                f"{'=' * 60}\n"
            )
        )
