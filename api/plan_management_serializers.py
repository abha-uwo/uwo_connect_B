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

    class Meta:
        model = Plan
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

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
