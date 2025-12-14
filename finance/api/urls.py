from django.urls import path, include
from rest_framework.routers import DefaultRouter

from finance.api.views import AccountViewSet, TransactionViewSet, transfer_api

router = DefaultRouter()
router.register("accounts", AccountViewSet, basename="accounts")
router.register("transactions", TransactionViewSet, basename="transactions")

urlpatterns = [
    path("", include(router.urls)),
    path("transfers/", transfer_api, name="transfer_api"),
]
