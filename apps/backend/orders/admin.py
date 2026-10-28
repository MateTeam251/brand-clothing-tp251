from decimal import Decimal
from django import forms

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet
from django.utils.html import format_html
from rest_framework.exceptions import ValidationError as DRFValidationError

from orders.email_services import send_order_status_changed_email
from orders.exceptions import PaymentProviderUnavailable
from orders.models import OrderItem, Order
from orders.references import build_order_reference
from orders.services import recalculate_order_totals, fill_order_item_snapshot, retry_payment
from payments.models import Payment


class OrderItemAdminForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = (
            "product",
            "product_name",
            "size",
            "quantity",
            "fabric_composition_ua",
            "fabric_composition_eng",
            "price_at_purchase",
            "discount_percent_at_purchase",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in (
                "product_name",
                "fabric_composition_ua",
                "fabric_composition_eng",
                "price_at_purchase",
                "discount_percent_at_purchase",
        ):
            if name in self.fields:
                self.fields[name].required = False
                self.fields[name].help_text = "Leave empty to take from the product."


class OrderItemInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if self.instance.pk or any(self.errors):
            return
        if not any(f.cleaned_data and not f.cleaned_data.get("DELETE") for f in self.forms):
            raise ValidationError("Add at least one item.")


class OrderItemInline(admin.TabularInline):
    """
    Items can be entered only while creating an order.
    After that they are read-only: corrections go into `admin_comment`
    or into a new order.
    """

    model = OrderItem
    form = OrderItemAdminForm
    formset = OrderItemInlineFormSet
    extra = 0

    create_fields = (
        "product",
        "product_name",
        "size",
        "quantity",
        "fabric_composition_ua",
        "fabric_composition_eng",
        "price_at_purchase",
        "discount_percent_at_purchase",
    )
    view_fields = create_fields + (
        "unit_price_after_discount", "line_subtotal", "line_total",
    )

    autocomplete_fields = ("product",)

    def get_fields(self, request, obj=None):
        return self.create_fields if obj is None else self.view_fields

    def get_readonly_fields(self, request, obj=None):
        return () if obj is None else self.view_fields

    def has_add_permission(self, request, obj=None):
        return obj is None

    def has_delete_permission(self, request, obj=None):
        return False


class PaymentInline(admin.TabularInline):
    """
    All payment attempts of the order, with a link to each payment.
    """

    model = Payment
    extra = 0
    can_delete = False
    show_change_link = True
    ordering = ("-created_at",)

    fields = (
        "provider_order_reference",
        "status",
        "amount",
        "currency",
        "created_at",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order_reference",
        "first_name",
        "last_name",
        "email",
        "status",
        "currency",
        "total_amount",
        "created_at",
    )

    list_filter = (
        "status",
        "currency",
        "created_at",
    )

    search_fields = (
        "id",
        "order_reference",
        "email",
        "first_name",
        "last_name",
        "user_phone",
        "user__email",
    )

    raw_id_fields = ("user",)
    ordering = ("-created_at",)
    inlines = (OrderItemInline, PaymentInline)

    always_readonly = (
        "order_reference",
        "subtotal",
        "discount_amount",
        "total_amount",
        "created_at",
        "updated_at",
    )

    readonly_after_create = (
        "user",
        "currency",
    )

    fieldsets = (
        (
            "Customer Info",
            {
                "fields": (
                    "user",
                    "first_name",
                    "last_name",
                    "user_phone",
                    "email",
                    "delivery_address",
                )
            },
        ),
        (
            "Financial Details",
            {
                "fields": (
                    "currency",
                    "subtotal",
                    "discount_amount",
                    "total_amount",
                )
            },
        ),
        (
            "Fulfillment & Delivery",
            {
                "fields": (
                    "status",
                    "delivery_provider",
                    "delivery_data",
                )
            }
        ),
        (
            "Internal",
            {
                "fields": (
                    "admin_comment",
                )
            }
        ),
        (
            "System",
            {
                "fields": (
                    "order_reference",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    actions = ("generate_payment_link",)

    @admin.action(description="Generate WayForPay payment link")
    def generate_payment_link(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Select exactly one order.", level=messages.ERROR)
            return

        order = queryset.first()

        try:
            _, _, payment_url = retry_payment(order_id=order.pk)
        except (DRFValidationError, PaymentProviderUnavailable) as e:
            error_msg = getattr(e, "detail", str(e))
            self.message_user(
                request,
                f"{order.order_reference}: {error_msg}",
                level=messages.ERROR,
            )
            return

        self.message_user(
            request,
            format_html(
                '{}: <a href="{}" target="_blank">payment link</a> (valid about 15 minutes)',
                order.order_reference,
                payment_url
            )
        )

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return self.always_readonly
        return self.always_readonly + self.readonly_after_create

    def save_model(self, request, obj: Order, form, change):
        if not change:
            obj.subtotal = Decimal("0.00")
            obj.discount_amount = Decimal("0.00")
            obj.total_amount = Decimal("0.00")
            super().save_model(request, obj, form, change)
            obj.order_reference = build_order_reference(obj.pk)
            obj.save(update_fields=["order_reference"])
            form.instance.order_reference = obj.order_reference
            return

        old_status = None
        if change and "status" in form.changed_data:
            old_status = Order.objects.only("status").get(pk=obj.pk).status

        super().save_model(request, obj, form, change)

        if old_status is not None and old_status != obj.status:
            send_order_status_changed_email(obj)
