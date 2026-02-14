from zoneinfo import ZoneInfo

from django.conf import settings
from jinja2 import FileSystemLoader, TemplateNotFound
from jinja2.sandbox import SandboxedEnvironment
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from ..models import CreditCard, CreditTransaction
from ..parsers import SUPPORTED_PARSERS


class CreditCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCard
        fields = ['id', 'name', 'card_no', 'exp_date', 'def_parser', 'def_grouper', 'act_ind']

        read_only_fileds = ['id']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditTransaction
        fields = ['id', 'credit_card', 'txn_date', 'txn_desc', 'grp_name', 'amt', 'is_credit', 'src_file']

    read_only_fileds = ['id']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        local_dt = instance.txn_date.astimezone(ZoneInfo(settings.USER_SETTINGS.get("Main", "home_tz")))
        representation['txn_date'] = local_dt.isoformat()

        return representation


class TransactionFileUploadSerializer(serializers.Serializer):
    credit_card = serializers.IntegerField()
    dt_format = serializers.CharField()
    parser = serializers.CharField(max_length=20)
    grouper = serializers.CharField(max_length=40, allow_blank=True, default='')
    file = serializers.FileField()

    def validate_credit_card(self, value):
        user = self.context['request'].user
        try:
            credit_card = CreditCard.objects.get(pk=value, user=user)
        except CreditCard.DoesNotExist:
            raise PermissionDenied("Account does not exist or doesn't belong to you")
        return credit_card

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

        allowed_mime_types = ["text/csv"]
        if value.content_type not in allowed_mime_types:
            raise serializers.ValidationError("Invalid File")

        return value
