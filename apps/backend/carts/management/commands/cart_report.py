from datetime import date

from django.core.management.base import BaseCommand, CommandError

from carts.reports import previous_week_start, upload_weekly_cart_report
from carts.services import mark_abandoned_carts


class Command(BaseCommand):
    help = "Marks abandoned carts and/or uploads the weekly cart report to S3 (same as the Celery tasks)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--week",
            help="Monday of the week to report, e.g. 2026-09-21. Defaults to the previous week.",
        )
        parser.add_argument(
            "--mark-abandoned",
            action="store_true",
            help="Mark abandoned carts before building the report.",
        )
        parser.add_argument(
            "--no-upload",
            action="store_true",
            help="Only mark abandoned carts, do not build the report.",
        )

    def handle(self, *args, **options):
        if options["mark_abandoned"] or options["no_upload"]:
            marked = mark_abandoned_carts()
            self.stdout.write(f"Marked {marked} carts as abandoned")

        if options["no_upload"]:
            return

        try:
            week_start = date.fromisoformat(options["week"]) if options["week"] else previous_week_start()
            names = upload_weekly_cart_report(week_start)
        except ValueError as exc:
            raise CommandError(str(exc))

        for name in names:
            self.stdout.write(self.style.SUCCESS(f"Uploaded {name}"))
