from zoneinfo import ZoneInfo

from django.conf import settings
from jinja2 import FileSystemLoader
from jinja2.exceptions import TemplateNotFound
from jinja2.sandbox import SandboxedEnvironment
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

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

    read_only_fields = ['id']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        local_txn_dt = instance.txn_date.astimezone(ZoneInfo(settings.USER_SETTINGS.get("Main", "home_tz")))
        local_opr_dt = instance.opr_dt.astimezone(ZoneInfo(settings.USER_SETTINGS.get("Main", "home_tz")))
        representation['txn_date'] = local_txn_dt.isoformat()
        representation['opr_dt'] = local_opr_dt.isoformat()

        return representation


class TransactionFileUploadSerializer(serializers.Serializer):
    account = serializers.IntegerField()
    dt_format = serializers.CharField()
    parser = serializers.CharField(max_length=20)
    grouper = serializers.CharField(max_length=40)
    file = serializers.FileField()

    def validate_account(self, value):
        user = self.context['request'].user
        try:
            account = Account.objects.get(pk=value, user=user)
        except Account.DoesNotExist:
            raise PermissionDenied("Account does not exist or doesn't belong to you")
        return account

    def validate_parser(self, value):
        if (value not in SUPPORTED_PARSERS.keys()) or value == "NULL":
            raise serializers.ValidationError("Unknown Parser")
        return value

    def validate_grouper(self, value):
        if value in ("NULL", ""):
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


class RerunGroupSerializer(serializers.Serializer):
    grouper = serializers.CharField(max_length=40)
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

    def validate(self, attrs):
        if self.context['request'].user != self.context['file'].user:
            raise PermissionDenied("File does not belong to you")
        return attrs


class TransactionByDateSerializer(serializers.Serializer):
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    txn_desc = serializers.CharField(max_length=1024, default='')

    def validate(self, attrs):
        if attrs["from_date"] > attrs["to_date"]:
            raise serializers.ValidationError("From Date must be before To Date")

        return attrs
