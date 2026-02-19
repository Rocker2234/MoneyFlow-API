from django_filters.rest_framework import FilterSet

from moneyflow.models import CreditTransaction, Transaction


class CreditTransactionFilter(FilterSet):
    class Meta:
        model = CreditTransaction
        fields = {
            'txn_date': ['lt', 'gt'],
            'amt': ['lt', 'gt'],
            'is_credit': ['exact'],
            'src_file': ['in'],
            'credit_card': ['in'],
        }


class AccTransactionFilter(FilterSet):
    class Meta:
        model = Transaction
        fields = {
            'txn_date': ['lt', 'gt'],
            'opr_dt': ['lt', 'gt'],
            'dbt_amount': ['lt', 'gt'],
            'cr_amount': ['lt', 'gt'],
            'cf_amt': ['lt', 'gt'],
            'src_file': ['in'],
            'account': ['in'],
        }
