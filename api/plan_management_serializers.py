from rest_framework import serializers
from .serializers import ObjectIdField
from .models import Feature, Plan, PlanFeature, ClientFeatureOverride, PlanAuditLog

# ── PLAN MANAGEMENT SERIALIZERS ─────────────────────────────────────

class FeatureSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)

    class Meta:
        model = Feature
        fields = '__all__'

class PlanSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    feature_keys = serializers.SerializerMethodField()
    channel_count = serializers.SerializerMethodField()
    connector_count = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_feature_keys(self, obj):
        if obj.metadata and isinstance(obj.metadata, dict):
            return obj.metadata.get('feature_keys', [])
        return []

    def get_channel_count(self, obj):
        keys = self.get_feature_keys(obj)
        return len([k for k in keys if k.startswith('channel_')])

    def get_connector_count(self, obj):
        keys = self.get_feature_keys(obj)
        return len([k for k in keys if k.startswith('connector_')])

    def create(self, validated_data):
        feature_keys = self.initial_data.get('feature_keys', None)
        metadata = validated_data.get('metadata', {}) or {}
        if feature_keys is not None:
            metadata['feature_keys'] = feature_keys
        validated_data['metadata'] = metadata
        return super().create(validated_data)

    def update(self, instance, validated_data):
        feature_keys = self.initial_data.get('feature_keys', None)
        if feature_keys is not None:
            metadata = instance.metadata or {}
            metadata['feature_keys'] = feature_keys
            instance.metadata = metadata
        return super().update(instance, validated_data)

class PlanFeatureSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)

    class Meta:
        model = PlanFeature
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class ClientFeatureOverrideSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)

    class Meta:
        model = ClientFeatureOverride
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class PlanAuditLogSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)

    class Meta:
        model = PlanAuditLog
        fields = '__all__'
        read_only_fields = ('timestamp',)
