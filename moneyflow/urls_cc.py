from django.urls import path, include
from rest_framework_nested.routers import DefaultRouter, NestedDefaultRouter

from .views import common, creditcard

cc_router = DefaultRouter()
cc_router.register('', creditcard.CreditCardViewSet, 'cc')

cc_transaction_router = NestedDefaultRouter(cc_router, '', lookup='cc')
cc_transaction_router.register('transactions', creditcard.TransactionViewSet, 'cc_transaction')

urlpatterns = [
    path('', include(cc_router.urls)),
    path('', include(cc_transaction_router.urls)),

    # File Related Paths
    path('parsers/', common.get_parsers, name='get_parsers'),
]
