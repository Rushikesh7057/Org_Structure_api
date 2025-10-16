from rest_framework import serializers
from .models import Asset


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            'id', 'uuid', 'asset_name', 'asset_type',
            'hierarchy_level', 'parent', 'description',
            'start_date', 'end_date', 'is_active'
        ]
        read_only_fields = ['id', 'uuid']

    def validate(self, attrs):
        asset_type = attrs.get('asset_type')
        parent = attrs.get('parent')

        if asset_type == 'organization' and parent is not None:
            raise serializers.ValidationError("An Organization cannot have a parent asset.")
        if asset_type != 'organization' and parent is None:
            raise serializers.ValidationError(f"A {asset_type} must have a parent asset.")

        return attrs
