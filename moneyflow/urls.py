from django.urls import path

from . import views

urlpatterns = [
    # TEST COnnection
    path('test/', views.check_conn, name='Test-Connection'),

    # Account Related Paths
    path('add_account/', views.add_account, name='Add-Account'),
    path('account/<int:acc_id>/', views.account, name='Account'),

    # path('add_transaction/', views.add_transaction, name='Add-Transaction'),

    # File Related Paths
    path('parsers/', views.get_parsers, name='Get-Parsers'),
    path('upload/transactions/', views.upload_transaction_file, name='Upload-Transaction-File'),
    path('regroup/<int:file_id>', views.rerun_grouper, name='Rerun-Grouper'),
    path('edit/transaction/<int:txn_id>/', views.edit_transaction, name='Edit-Transaction'),
    path('delete/<int:file_id>/', views.delete_uploaded_file, name='Delete-Transaction-File'),
    path('transactions/by_files', views.get_transactions_by_file, name='Get-Transaction-For-Files'),
    path('transactions/filter', views.get_transactions_filtered, name='Get-Transaction-For-Date '),
]
