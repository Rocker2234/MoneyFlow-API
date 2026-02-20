from zoneinfo import ZoneInfo

from django.conf import settings
from jinja2 import FileSystemLoader
from jinja2.exceptions import TemplateNotFound
from jinja2.sandbox import SandboxedEnvironment
from rest_framework import serializers

from ..models import Account, Transaction
from ..parsers import SUPPORTED_PARSERS


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'name', 'acc_no', 'ifsc_code', 'acc_type', 'currency', 'min_bal', 'dis_bal', 'def_parser',
                  'def_grouper', 'act_ind']

    read_only_fields = ['id']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'account', 'txn_date', 'txn_desc', 'grp_name', 'opr_dt', 'dbt_amount', 'cr_amount', 'ref_num',
                  'cf_amt', 'src_file']

    read_only_fields = ['id', 'account', 'txn_date', 'txn_desc', 'opr_dt', 'dbt_amount', 'cr_amount', 'ref_num',
                        'cf_amt', 'src_file']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        local_txn_dt = instance.txn_date.astimezone(ZoneInfo(settings.USER_SETTINGS.get("Main", "home_tz")))
        local_opr_dt = instance.opr_dt.astimezone(ZoneInfo(settings.USER_SETTINGS.get("Main", "home_tz")))
        representation['txn_date'] = local_txn_dt.isoformat()
        representation['opr_dt'] = local_opr_dt.isoformat()

        return representation


class TransactionFileUploadSerializer(serializers.Serializer):
    dt_format = serializers.CharField()
    parser = serializers.CharField(max_length=20, allow_blank=True, default='')
    grouper = serializers.CharField(max_length=40, allow_blank=True, default='')
    file = serializers.FileField()
    is_future_only = serializers.BooleanField(allow_null=True, default=False)
    is_strict_future = serializers.BooleanField(allow_null=True, default=False)

    def validate_parser(self, value):
        value = self.context['acc'].def_parser if not value else value

        if (value not in SUPPORTED_PARSERS.keys()) or value == "NULL":
            raise serializers.ValidationError("Unknown Parser")
        return value

    def validate_grouper(self, value):
        if value == "<skip>":
            return None

        value = self.context['acc'].def_grouper if not value else value
        if not value:
            return None

        try:
            template = SandboxedEnvironment(loader=FileSystemLoader(
                settings.USER_SETTINGS.get("Main", "templates"))).get_template('G_' + value + '.j2')
            return template
        except TemplateNotFound:
            raise serializers.ValidationError("Invalid Grouper")

    def validate_file(self, value):
        if value in ("NULL", "", None):
            raise serializers.ValidationError("File is required!")

        allowed_mime_types = ["text/plain", "application/vnd.ms-excel"]
        if value.content_type not in allowed_mime_types:
            raise serializers.ValidationError("Invalid File")

        return value

    def validate(self, attrs):
        if (not attrs["is_future_only"]) and attrs["is_strict_future"]:
            raise serializers.ValidationError("Future Only is required when using Strict Future.")
        return attrs


class RerunGroupSerializer(serializers.Serializer):
    grouper = serializers.CharField(max_length=40, allow_blank=True, default='')
    blanks_only = serializers.BooleanField()

    def validate_grouper(self, value):
        if value in ("NULL", ""):
            return None

        try:
            template = SandboxedEnvironment(loader=FileSystemLoader(
                settings.USER_SETTINGS.get("Main", "templates"))).get_template('G_' + value + '.j2')
            return template
        except TemplateNotFound:
            raise serializers.ValidationError("Invalid Grouper")


class TransactionByDateSerializer(serializers.Serializer):
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    txn_desc = serializers.CharField(max_length=1024, default='')

    def validate(self, attrs):
        if attrs["from_date"] > attrs["to_date"]:
            raise serializers.ValidationError("From Date must be before To Date")

        return attrs
