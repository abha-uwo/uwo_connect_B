from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from ..models import Feature, Plan, PlanFeature, ClientFeatureOverride, PlanAuditLog
from ..plan_management_serializers import (
    FeatureSerializer,
    PlanSerializer,
    PlanFeatureSerializer,
    ClientFeatureOverrideSerializer,
    PlanAuditLogSerializer,
)

class FeatureViewSet(viewsets.ModelViewSet):
    """CRUD operations for Feature model."""
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer

class PlanViewSet(viewsets.ModelViewSet):
    """CRUD operations for Plan model."""
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

class PlanFeatureViewSet(viewsets.ModelViewSet):
    """CRUD operations for PlanFeature model linking Features to Plans."""
    queryset = PlanFeature.objects.all()
    serializer_class = PlanFeatureSerializer

class ClientFeatureOverrideViewSet(viewsets.ModelViewSet):
    """CRUD for per-client feature overrides."""
    queryset = ClientFeatureOverride.objects.all()
    serializer_class = ClientFeatureOverrideSerializer

class PlanAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read‑only viewset for audit logs of plan changes."""
    queryset = PlanAuditLog.objects.all().order_by('-timestamp')
    serializer_class = PlanAuditLogSerializer
    # Optionally you could add filters for client/plan etc.
