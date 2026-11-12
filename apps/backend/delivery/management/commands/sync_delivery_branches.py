from django.core.management.base import BaseCommand, CommandError

from delivery.factory import SYNCED_PROVIDERS
from delivery.tasks import sync_provider_branches


class Command(BaseCommand):
    help = "Synchronizes the cached city/branch directory for delivery providers, synchronously (no Celery needed)."

    def add_arguments(self, parser):
        parser.add_argument(
            "provider",
            nargs="?",
            choices=SYNCED_PROVIDERS,
            help="Sync only this provider. Omit to sync all of them.",
        )

    def handle(self, *args, **options):
        providers = [options["provider"]] if options["provider"] else SYNCED_PROVIDERS

        for provider_code in providers:
            self.stdout.write(f"Syncing {provider_code}...")
            try:
                sync_provider_branches(provider_code)
            except Exception as exc:
                raise CommandError(f"Failed to sync {provider_code}: {exc}") from exc
            self.stdout.write(self.style.SUCCESS(f"Synced {provider_code}."))
