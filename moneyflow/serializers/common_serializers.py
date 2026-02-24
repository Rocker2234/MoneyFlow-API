from rest_framework import serializers

from ..models import FileAudit


class FileAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileAudit
        fields = ['id', 'file_name', 'to_id', 'op_desc', 'status', 'op_args', 'op_add_txt', 'isrt_dt']
        read_only_fields = ['id', 'file_name', 'to_id', 'op_desc', 'status', 'op_args', 'op_add_txt', 'isrt_dt']
