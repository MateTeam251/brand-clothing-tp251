from django.db import models


class Currency(models.TextChoices):
    UAH = "UAH", "UAH"
    USD = "USD", "USD"


class Size(models.TextChoices):
    XXS = "2XS", "2XS"
    XS = "XS", "XS"
    S = "S", "S"
    M = "M", "M"
    L = "L", "L"
    XL = "XL", "XL"
    XXL = "2XL", "2XL"
    XXXL = "3XL", "3XL"
    XXXXL = "4XL", "4XL"


class DeliveryProvider(models.TextChoices):
    NOVA_POSHTA = "NOVA_POSHTA", "Nova Poshta"
    UKRPOSHTA = "UKRPOSHTA", "Ukrposhta"
    DHL = "DHL", "DHL"


class AvailabilityRequestStatusEnum(models.TextChoices):
    NEW = "new", "New"
    CONTACTED = "contacted", "Contacted"
    CLOSED = "closed", "Closed"
