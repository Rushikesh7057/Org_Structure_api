# hierarchy/serializers.py
from rest_framework import serializers
from .models import Asset, AssetDetail

class AssetDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetDetail
        fields = ['location', 'building', 'floor', 'room', 'line']


class AssetSerializer(serializers.ModelSerializer):
    details = AssetDetailSerializer(required=False)

    class Meta:
        model = Asset
        fields = ['id', 'uuid', 'asset_name', 'asset_type', 'hierarchy_level',
                  'parent', 'description', 'start_date', 'end_date', 'is_active', 'details']
        read_only_fields = ['id', 'uuid']

    def validate(self, attrs):
        # Validate parent rules
        asset_type = attrs.get('asset_type')
        parent = attrs.get('parent')

        if asset_type == 'organization' and parent is not None:
            raise serializers.ValidationError("An Organization cannot have a parent asset.")
        if asset_type != 'organization' and parent is None:
            raise serializers.ValidationError(f"A {asset_type} must have a parent asset.")

        return attrs

    def create(self, validated_data):
        details_data = validated_data.pop('details', None)
        asset = Asset.objects.create(**validated_data)
        if details_data:
            AssetDetail.objects.create(asset=asset, **details_data)
        return asset

    def update(self, instance, validated_data):
        details_data = validated_data.pop('details', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if details_data:
            AssetDetail.objects.update_or_create(asset=instance, defaults=details_data)
        return instance
