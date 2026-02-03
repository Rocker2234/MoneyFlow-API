from rest_framework import serializers

from moneyflow.models import Account, Transaction


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'name', 'acc_no', 'ifsc_code', 'acc_type', 'min_bal', 'dis_bal', 'def_parser', 'def_grouper', 'act_ind']

    read_only_fields = ['id']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'account', 'txn_date', 'txn_desc', 'grp_name', 'opr_dt', 'dbt_amount', 'cr_amount', 'ref_num',
                  'cf_amt', 'src_file']

    read_only_fields = ['id']
