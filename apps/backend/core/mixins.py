

class LanguageMixin:
    """
    Gives a serializer the _lang() method for resolving the response
    language based on the ?lang= query parameter of the current request.

    Usage: inherit this mixin BEFORE serializers.ModelSerializer and call
    self._lang() inside get_<field>() methods that return translatable content.
    """
    def _lang(self):
        """
        Returns "eng" if the request explicitly passes ?lang=en.
        In all other cases (missing parameter, any other value)
        returns "ua" — Ukrainian is the default language.
        """
        request = self.context.get("request")
        lang = request.GET.get("lang", "ua") if request else "ua"
        return "eng" if lang == "en" else "ua"


class CurrencyMixin:
    """
    Gives a serializer the _currency() method for resolving the response
    currency based on the ?currency= query parameter of the current request.

    Usage: same as LanguageMixin — inherit before serializers.ModelSerializer
    and call self._currency() in methods that deal with price.
    """
    def _currency(self):
        """
        Returns "usd" if the request explicitly passes ?currency=usd.
        In all other cases returns "uah" — hryvnia is the default currency.
        """
        request = self.context.get("request")
        currency = request.GET.get("currency", "uah") if request else "uah"
        return "usd" if currency == "usd" else "uah"
