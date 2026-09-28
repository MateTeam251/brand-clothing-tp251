from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from carts.models import (
    AbandonedCartSnapshot,
    AbandonedCartSnapshotItem,
    Cart,
    CartStatusEnum,
)


def get_or_create_active_cart_for(*, user=None, session_key=None):
    """
    Returns the owner's active cart.

    If the owner has no active cart but has an abandoned one, that cart is
    brought back to ACTIVE instead of creating an empty one, so returning
    customers keep their items.
    """
    if user is not None:
        lookup = {"user": user}
    else:
        lookup = {"session_key": session_key, "user__isnull": True}

    cart = Cart.objects.filter(status=CartStatusEnum.ACTIVE, **lookup).first()
    if cart:
        return cart

    abandoned = (
        Cart.objects.filter(status=CartStatusEnum.ABANDONED, **lookup)
        .order_by("-abandoned_at")
        .first()
    )
    if abandoned:
        recover_abandoned_cart(abandoned)
        return abandoned

    cart, _ = Cart.objects.get_or_create(status=CartStatusEnum.ACTIVE, **lookup)
    return cart


@transaction.atomic
def recover_abandoned_cart(cart):
    """
    Moves an abandoned cart back to ACTIVE. The snapshot keeps the history and
    gets recovered_at, so reports can count how many abandoned carts came back.
    """
    now = timezone.now()

    AbandonedCartSnapshot.objects.filter(cart=cart, recovered_at__isnull=True).update(recovered_at=now)

    cart.status = CartStatusEnum.ACTIVE
    cart.abandoned_at = None
    cart.abandoned_value_uah = None
    cart.abandoned_value_usd = None
    # updated_at is bumped too, so the abandonment countdown starts over
    cart.save(update_fields=[
        "status", "abandoned_at", "abandoned_value_uah", "abandoned_value_usd", "updated_at",
    ])


def _price_after_discount(price, discount_percent):
    if not discount_percent:
        return price
    return (price * Decimal(100 - discount_percent) / Decimal("100")).quantize(Decimal("0.01"))


def mark_abandoned_carts(now=None):
    """
    Marks carts as ABANDONED: they have items, were not checked out and were
    not changed for CART_ABANDON_AFTER_HOURS. Saves a price snapshot for each.

    Returns the number of carts marked.
    """
    now = now or timezone.now()
    abandon_after = timedelta(hours=settings.CART_ABANDON_AFTER_HOURS)
    cutoff = now - abandon_after

    candidate_ids = list(
        Cart.objects.filter(
            status=CartStatusEnum.ACTIVE,
            updated_at__lt=cutoff,
            items__isnull=False,
        ).values_list("id", flat=True).distinct()
    )

    marked = 0
    for cart_id in candidate_ids:
        if _abandon_cart(cart_id, cutoff, abandon_after):
            marked += 1
    return marked


@transaction.atomic
def _abandon_cart(cart_id, cutoff, abandon_after):
    # Lock and re-check: the customer may have changed the cart since the candidate query.
    cart = (
        Cart.objects.select_for_update()
        .filter(pk=cart_id, status=CartStatusEnum.ACTIVE, updated_at__lt=cutoff)
        .first()
    )
    if cart is None:
        return False

    cart_items = list(cart.items.select_related("product"))
    if not cart_items:
        return False

    abandoned_at = cart.updated_at + abandon_after

    snapshot_items = []
    totals = {
        "items_count": 0,
        "value_uah": Decimal("0.00"),
        "value_usd": Decimal("0.00"),
        "value_uah_before_discount": Decimal("0.00"),
        "value_usd_before_discount": Decimal("0.00"),
    }

    for item in cart_items:
        product = item.product
        discount = int(product.discount_percent or 0)

        totals["items_count"] += item.quantity
        totals["value_uah_before_discount"] += product.price_uah * item.quantity
        totals["value_usd_before_discount"] += product.price_usd * item.quantity
        totals["value_uah"] += _price_after_discount(product.price_uah, discount) * item.quantity
        totals["value_usd"] += _price_after_discount(product.price_usd, discount) * item.quantity

        snapshot_items.append(AbandonedCartSnapshotItem(
            product=product,
            product_name=product.name,
            size=item.size,
            quantity=item.quantity,
            price_uah=product.price_uah,
            price_usd=product.price_usd,
            discount_percent=discount,
        ))

    snapshot = AbandonedCartSnapshot.objects.create(
        cart=cart,
        user=cart.user,
        is_guest=cart.user_id is None,
        cart_created_at=cart.created_at,
        last_activity_at=cart.updated_at,
        abandoned_at=abandoned_at,
        **totals,
    )
    for snapshot_item in snapshot_items:
        snapshot_item.snapshot = snapshot
    AbandonedCartSnapshotItem.objects.bulk_create(snapshot_items)

    # .update() on purpose: cart.save() would bump updated_at (auto_now).
    Cart.objects.filter(pk=cart.pk).update(
        status=CartStatusEnum.ABANDONED,
        abandoned_at=abandoned_at,
        abandoned_value_uah=totals["value_uah"],
        abandoned_value_usd=totals["value_usd"],
    )
    return True


def merge_guest_cart_into_user_cart(request, user):
    session_key = request.session.session_key
    if not session_key:
        return

    guest_carts = Cart.objects.filter(session_key=session_key, user__isnull=True)
    guest_cart = guest_carts.filter(status=CartStatusEnum.ACTIVE).first()
    if not guest_cart:
        guest_cart = (
            guest_carts.filter(status=CartStatusEnum.ABANDONED).order_by("-abandoned_at").first()
        )
        if not guest_cart:
            return
        recover_abandoned_cart(guest_cart)

    user_cart = get_or_create_active_cart_for(user=user)

    for item in guest_cart.items.select_related("product"):
        existing = user_cart.items.filter(product=item.product, size=item.size).first()
        if existing:
            existing.quantity += item.quantity
            existing.save(update_fields=["quantity"])
        else:
            item.cart = user_cart
            item.save(update_fields=["cart"])

    guest_cart.delete()
    user_cart.save(update_fields=["updated_at"])
