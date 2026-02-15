from django_filters.rest_framework import FilterSet

from moneyflow.models import CreditTransaction


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
