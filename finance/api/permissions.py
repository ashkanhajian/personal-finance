from rest_framework.permissions import BasePermission

class IsCustomerOwner(BasePermission):
    """
    Object-level permission: object must belong to request.user's customer_profile.
    Assumes:
      - Account has .customer
      - Transaction has .account.customer
    """
    def has_object_permission(self, request, view, obj):
        customer = getattr(request.user, "customer_profile", None)
        if customer is None:
            return False

        if hasattr(obj, "customer"):
            return obj.customer_id == customer.id

        # Transaction-like
        if hasattr(obj, "account"):
            return obj.account.customer_id == customer.id

        return False
