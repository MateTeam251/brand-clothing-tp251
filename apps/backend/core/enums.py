from django.db import models


class Currency(models.TextChoices):
    UAH = "UAH", "UAH"
    USD = "USD", "USD"


class Size(models.TextChoices):
    XS = "XS", "XS"
    S = "S", "S"
    M = "M", "M"
    L = "L", "L"
    XL = "XL", "XL"


class DeliveryProvider(models.TextChoices):
    NOVA_POSHTA = "NOVA_POSHTA", "Nova Poshta"
    UKRPOSHTA = "UKRPOSHTA", "Ukrposhta"
    DHL = "DHL", "DHL"
