"""
Set request.customer for storefront when store is set and session has customer_id for this store.
"""
from .models import Customer

SESSION_CUSTOMER_KEY_PREFIX = "customer_id_"


def _customer_session_key(store_id):
    return f"{SESSION_CUSTOMER_KEY_PREFIX}{store_id}"


class CustomerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.customer = None
        store = getattr(request, "store", None)
        if store:
            key = _customer_session_key(store.pk)
            customer_id = request.session.get(key)
            if customer_id:
                try:
                    request.customer = Customer.objects.get(pk=customer_id, store=store)
                except Customer.DoesNotExist:
                    request.session.pop(key, None)
        return self.get_response(request)
