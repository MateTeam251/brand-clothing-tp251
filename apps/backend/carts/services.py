from carts.models import Cart, CartStatusEnum


def merge_guest_cart_into_user_cart(request, user):
    session_key = request.session.session_key
    if not session_key:
        return

    guest_cart = Cart.objects.filter(
        session_key=session_key, user__isnull=True, status=CartStatusEnum.ACTIVE,
    ).first()
    if not guest_cart:
        return

    user_cart, _ = Cart.objects.get_or_create(user=user, status=CartStatusEnum.ACTIVE)

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
