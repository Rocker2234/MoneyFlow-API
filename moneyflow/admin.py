from django.contrib import admin
from django.db.models.aggregates import Count
from django.utils.html import format_html, urlencode
from django.urls import reverse

from . import models


@admin.register(models.Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'ifsc_code', 'min_bal', 'dis_bal', 'txns')
    list_editable = ('dis_bal',)
    search_fields = ('name', 'acc_no')

    @admin.display(ordering='transactions_count', description='Transactions')
    def txns(self, account):
        url = (reverse('admin:moneyflow_transaction_changelist') +
               '?' + urlencode({
                    'transaction__account': str(account.id),
                }))
        return format_html("<a href='{}'>{}</a>", url, account.transactions_count)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            transactions_count=Count('transactions')
        )


@admin.register(models.Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('txn_desc', 'grp_name', 'txn_date', 'dbt_amount', 'cr_amount', 'cf_amt', 'acc_name', 'file_name')
    list_select_related = ('account',)
    list_filter = ('account',)
    search_fields = ('txn_desc', 'grp_name', 'txn_date', 'dbt_amount', 'cr_amount', 'cf_amt', 'acc_name', 'file_name')

    @admin.display(ordering='account', description='Account')
    def acc_name(self, transaction):
        url = reverse('admin:moneyflow_account_changelist')
        return format_html("<a href='{}'>{}</a>", url, transaction.account)

    @admin.display(ordering='src_file', description='File')
    def file_name(self, transaction):
        url = reverse('admin:moneyflow_fileaudit_changelist')
        return format_html("<a href='{}'>{}</a>", url, transaction.src_file)


@admin.register(models.CreditCard)
class CreditCardAdmin(admin.ModelAdmin):
    list_display = ('name', 'card_no', 'exp_date', 'credit_transactions')
    search_fields = ('name',)

    @admin.display(ordering='credit_transactions', description='Credit Transactions')
    def credit_transactions(self, credit_card):
        return credit_card.transaction_count

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            transaction_count=Count('credit_transactions')
        )


@admin.register(models.CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ('txn_desc', 'txn_date', 'amt', 'card_name')
    list_filter = ('credit_card',)
    search_fields = ('txn_desc', 'txn_date', 'amt', 'card_name')

    @admin.display(ordering='credit_card', description='Card')
    def card_name(self, credit_transaction):
        url = reverse('admin:moneyflow_creditcard_changelist')
        return format_html("<a href='{}'>{}</a>", url, credit_transaction.credit_card)


@admin.register(models.FileAudit)
class FileAuditAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'op_desc', 'to_id', 'status', 'isrt_dt')
