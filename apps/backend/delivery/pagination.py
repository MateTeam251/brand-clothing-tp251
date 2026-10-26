from rest_framework.pagination import LimitOffsetPagination


class FixedLimitOffsetPagination(LimitOffsetPagination):
    """
    Always returns `default_limit` items: the client's `limit` is ignored,
    only `offset` moves through the pages.
    """

    default_limit = 30

    def get_limit(self, request):
        return self.default_limit

    def get_schema_operation_parameters(self, view):
        # Hide `limit` from Swagger, it has no effect.
        return [
            parameter for parameter in super().get_schema_operation_parameters(view)
            if parameter["name"] != self.limit_query_param
        ]


class DeliveryCityPagination(FixedLimitOffsetPagination):
    pass


class DeliveryBranchPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 50
