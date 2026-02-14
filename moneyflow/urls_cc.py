from django.urls import path

from .views import common, creditcard

urlpatterns = [
    path('add/', creditcard.add_card, name='add_cc'),
    path('<int:cc_id>/', creditcard.credit_card, name='get_cc'),

    # File Related Paths
    path('parsers/', common.get_parsers, name='get_parsers'),
    path('transactions/upload/', creditcard.upload_transaction_file, name='upload_cc_transaction_file'),
    path('transaction/edit/<int:txn_id>/', creditcard.edit_transaction, name='edit_cc_transaction'),
    path('transactions/delete/<int:file_id>/', common.delete_uploaded_file, name='delete_cc_transaction_file'),
    path('transactions/by_files/', creditcard.get_transactions_by_file, name='get_cc_transaction_for_files'),
]
