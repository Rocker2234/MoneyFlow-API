from django.urls import path

from .views import account, common

urlpatterns = [
    # Account Related Paths
    path('add/', account.add_account, name='add_account'),
    path('<int:acc_id>/', account.account, name='account'),

    # File Related Paths
    path('parsers/', common.get_parsers, name='get_parsers'),
    path('transactions/upload/', account.upload_transaction_file, name='upload_account_transaction_file'),
    path('transactions/regroup/<int:file_id>/', account.rerun_grouper, name='rerun_grouper'),
    path('transactions/by_files/', account.get_transactions_by_file, name='get_account_transaction_for_files'),
    path('transactions/filter/', account.get_transactions_filtered, name='get_account_transaction_filtered'),
    path('transaction/edit/<int:txn_id>/', account.edit_transaction, name='edit_account_transaction'),
    path('transactions/delete/<int:file_id>/', common.delete_uploaded_file, name='delete_account_transaction_file'),
]
