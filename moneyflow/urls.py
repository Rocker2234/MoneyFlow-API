from django.urls import path, include
from rest_framework_nested.routers import DefaultRouter, NestedDefaultRouter

from .views import common, account, creditcard

# Account Router
acc_router = DefaultRouter()
acc_router.register('accounts', account.AccountViewSet, basename='account')

acc_transaction = NestedDefaultRouter(acc_router, 'accounts', lookup='acc')
acc_transaction.register('transactions', account.TransactionViewSet, basename='acc_transaction')

# Credit Card Router
cc_router = DefaultRouter()
cc_router.register('creditcards', creditcard.CreditCardViewSet, 'cc')

cc_transaction_router = NestedDefaultRouter(cc_router, 'creditcards', lookup='cc')
cc_transaction_router.register('transactions', creditcard.TransactionViewSet, 'cc_transaction')

urlpatterns = [
    path('parsers/', common.get_parsers, name='get_parsers'),
    path('', include(acc_router.urls)),
    path('', include(cc_router.urls)),
    path('', include(acc_transaction.urls)),
    path('', include(cc_transaction_router.urls)),
]
