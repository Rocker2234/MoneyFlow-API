from django_filters.rest_framework import FilterSet
from rest_framework.filters import SearchFilter

from .models import CreditTransaction, Transaction, FileAudit


class CreditSearchFilter(SearchFilter):
    def get_search_fields(self, view, request):
        if getattr(view, 'action', None) == 'all_transactions':
            return ['txn_desc', 'grp_name']
        return ['name', 'card_no']


class CreditTransactionFilter(FilterSet):
    class Meta:
        model = CreditTransaction
        fields = {
            'txn_date': ['lte', 'gte'],
            'amt': ['lte', 'gte'],
            'is_credit': ['exact'],
            'src_file': ['in'],
            'credit_card': ['in'],
        }


class AccSearchFilter(SearchFilter):
    def get_search_fields(self, view, request):
        if getattr(view, 'action', None) == 'all_transactions':
            return ['txn_desc', 'grp_name']
        return ['name', 'acc_no', 'ifsc_code']


class AccTransactionFilter(FilterSet):
    class Meta:
        model = Transaction
        fields = {
            'txn_date': ['lte', 'gte'],
            'opr_dt': ['lte', 'gte'],
            'dbt_amount': ['lte', 'gte'],
            'cr_amount': ['lte', 'gte'],
            'cf_amt': ['lte', 'gte'],
            'src_file': ['in'],
            'account': ['in'],
        }


class AuditFileFilter(FilterSet):
    class Meta:
        model = FileAudit
        fields = {
            'isrt_dt': ['lte', 'gte'],
        }
