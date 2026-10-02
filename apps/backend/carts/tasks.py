import logging
from datetime import date

from celery import shared_task

from carts.reports import previous_week_start, upload_weekly_cart_report
from carts.services import mark_abandoned_carts

logger = logging.getLogger(__name__)


@shared_task
def mark_abandoned_carts_task():
    marked = mark_abandoned_carts()
    logger.info("Marked %s carts as abandoned", marked)
    return marked


@shared_task
def send_weekly_cart_report_task(week_start=None):
    """
    week_start: ISO date of a Monday ("2026-09-21"). Defaults to the previous week.
    """
    start = date.fromisoformat(week_start) if week_start else previous_week_start()
    names = upload_weekly_cart_report(start)
    logger.info("Uploaded weekly cart report: %s", ", ".join(names))
    return names
