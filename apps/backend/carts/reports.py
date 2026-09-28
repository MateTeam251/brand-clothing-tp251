"""
Weekly cart report for data analysts.

Two CSV files per ISO week are uploaded to ANALYTICS_REPORTS_BUCKET:
  <prefix>/<YYYY-Www>/summary.csv          one row with the week's totals
  <prefix>/<YYYY-Www>/abandoned_items.csv  one row per item of every cart abandoned that week

Weeks run Monday 00:00 to next Monday 00:00 in TIME_ZONE.
"""

import csv
import io
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.db.models import Count, Q, Sum
from django.utils import timezone
from storages.backends.s3 import S3Storage

from carts.models import AbandonedCartSnapshot, AbandonedCartSnapshotItem, Cart
from orders.models import Order, OrderStatus

PAID_ORDER_STATUSES = [
    OrderStatus.PAID,
    OrderStatus.AWAITING_SHIPMENT,
    OrderStatus.SHIPPED,
    OrderStatus.DELIVERED,
]

SUMMARY_FIELDS = [
    "week",
    "period_start",
    "period_end",
    "carts_created",
    "carts_created_guest",
    "carts_created_registered",
    "abandoned_carts",
    "abandoned_carts_guest",
    "abandoned_carts_registered",
    "abandoned_value_uah",
    "abandoned_value_uah_before_discount",
    "abandoned_value_usd",
    "abandoned_value_usd_before_discount",
    "recovered_carts",
    "orders_created",
    "orders_paid",
    "orders_guest",
    "orders_registered",
    "new_users",
    "new_users_activated",
]

ITEM_FIELDS = [
    "week",
    "snapshot_id",
    "abandoned_at",
    "is_guest",
    "product_id",
    "product_name",
    "size",
    "quantity",
    "price_uah",
    "price_usd",
    "discount_percent",
]


def previous_week_start(today=None):
    today = today or timezone.localdate()
    return today - timedelta(days=today.weekday() + 7)


def week_bounds(week_start: date):
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(week_start, time.min), tz)
    return start, start + timedelta(days=7)


def week_label(week_start: date):
    year, week, _ = week_start.isocalendar()
    return f"{year}-W{week:02d}"


def build_summary(week_start: date):
    start, end = week_bounds(week_start)
    in_week = {"created_at__gte": start, "created_at__lt": end}

    carts = (
        Cart.objects.filter(**in_week, items__isnull=False)
        .aggregate(
            total=Count("id", distinct=True),
            guest=Count("id", distinct=True, filter=Q(user__isnull=True)),
        )
    )

    snapshots = AbandonedCartSnapshot.objects.filter(abandoned_at__gte=start, abandoned_at__lt=end)
    abandoned = snapshots.aggregate(
        total=Count("id"),
        guest=Count("id", filter=Q(is_guest=True)),
        value_uah=Sum("value_uah"),
        value_uah_before_discount=Sum("value_uah_before_discount"),
        value_usd=Sum("value_usd"),
        value_usd_before_discount=Sum("value_usd_before_discount"),
    )

    orders = Order.objects.filter(**in_week).aggregate(
        total=Count("id"),
        paid=Count("id", filter=Q(status__in=PAID_ORDER_STATUSES)),
        guest=Count("id", filter=Q(user__isnull=True)),
    )

    users = get_user_model().objects.filter(
        is_staff=False, date_joined__gte=start, date_joined__lt=end,
    ).aggregate(
        total=Count("id"),
        activated=Count("id", filter=Q(is_active=True)),
    )

    zero = Decimal("0.00")
    return {
        "week": week_label(week_start),
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "carts_created": carts["total"],
        "carts_created_guest": carts["guest"],
        "carts_created_registered": carts["total"] - carts["guest"],
        "abandoned_carts": abandoned["total"],
        "abandoned_carts_guest": abandoned["guest"],
        "abandoned_carts_registered": abandoned["total"] - abandoned["guest"],
        "abandoned_value_uah": abandoned["value_uah"] or zero,
        "abandoned_value_uah_before_discount": abandoned["value_uah_before_discount"] or zero,
        "abandoned_value_usd": abandoned["value_usd"] or zero,
        "abandoned_value_usd_before_discount": abandoned["value_usd_before_discount"] or zero,
        "recovered_carts": AbandonedCartSnapshot.objects.filter(
            recovered_at__gte=start, recovered_at__lt=end,
        ).count(),
        "orders_created": orders["total"],
        "orders_paid": orders["paid"],
        "orders_guest": orders["guest"],
        "orders_registered": orders["total"] - orders["guest"],
        "new_users": users["total"],
        "new_users_activated": users["activated"],
    }


def build_abandoned_items(week_start: date):
    start, end = week_bounds(week_start)
    label = week_label(week_start)
    items = (
        AbandonedCartSnapshotItem.objects.filter(
            snapshot__abandoned_at__gte=start, snapshot__abandoned_at__lt=end,
        )
        .select_related("snapshot")
        .order_by("snapshot__abandoned_at", "id")
    )
    return [
        {
            "week": label,
            "snapshot_id": item.snapshot_id,
            "abandoned_at": item.snapshot.abandoned_at.isoformat(),
            "is_guest": item.snapshot.is_guest,
            "product_id": item.product_id,
            "product_name": item.product_name,
            "size": item.size,
            "quantity": item.quantity,
            "price_uah": item.price_uah,
            "price_usd": item.price_usd,
            "discount_percent": item.discount_percent,
        }
        for item in items
    ]


def to_csv(fieldnames, rows):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def get_reports_storage():
    if not settings.ANALYTICS_REPORTS_BUCKET:
        raise ImproperlyConfigured("ANALYTICS_REPORTS_BUCKET is not set.")
    return S3Storage(
        bucket_name=settings.ANALYTICS_REPORTS_BUCKET,
        location=settings.ANALYTICS_REPORTS_PREFIX,
        file_overwrite=True,  # re-running a week replaces its files
    )


def upload_weekly_cart_report(week_start: date, storage=None):
    """
    Builds the report for the week starting on week_start (a Monday) and
    uploads both CSV files. Returns the saved file names.
    """
    if week_start.weekday() != 0:
        raise ValueError(f"week_start must be a Monday, got {week_start}")

    storage = storage or get_reports_storage()
    label = week_label(week_start)

    files = {
        f"{label}/summary.csv": to_csv(SUMMARY_FIELDS, [build_summary(week_start)]),
        f"{label}/abandoned_items.csv": to_csv(ITEM_FIELDS, build_abandoned_items(week_start)),
    }
    return [storage.save(name, ContentFile(content.encode("utf-8"))) for name, content in files.items()]
