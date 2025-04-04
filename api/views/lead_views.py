# api/views/lead_views.py

from django.db.models import Q
from django.utils.timezone import now, timedelta
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.models import Lead, LeadStatus
from api.serializers import LeadSerializer, LeadStatusUpdateSerializer


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    # ✅ Action pour mettre à jour uniquement le statut
    @action(detail=True, methods=["patch"], url_path="set-status")
    def set_status(self, request, pk=None):
        lead = self.get_object()
        serializer = LeadStatusUpdateSerializer(lead, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": serializer.data["status"]}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="statut-nouveau")
    def get_nouveaux_leads(self, request):
        count = Lead.objects.filter(status=LeadStatus.NOUVEAU).count()
        return Response({"count": count})

    @action(detail=False, methods=["get"], url_path="rdv-demain")
    def get_leads_rdv_demain(self, request):
        tomorrow = now().date() + timedelta(days=1)
        count = Lead.objects.filter(appointment_date__date=tomorrow).count()
        return Response({"count": count})

    @action(detail=False, methods=["get"], url_path="statut-absent")
    def get_leads_absents(self, request):
        count = Lead.objects.filter(status=LeadStatus.ABSENT).count()
        return Response({"count": count})

    @action(detail=False, methods=["post"], url_path="maj-absents-auto")
    def maj_leads_absents_auto(self, request):
        limite = now() - timedelta(hours=1)
        leads = Lead.objects.filter(status=LeadStatus.RDV_CONFIRME, appointment_date__lt=limite)
        updated = leads.update(status=LeadStatus.ABSENT)
        return Response({"message": f"{updated} leads mis à jour en 'absent'"})

    @action(detail=False, methods=["get"], url_path="search")
    def search_leads(self, request):
        query = request.query_params.get("q", "")
        if not query:
            return Response([])

        leads = Lead.objects.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
        )[:10]
        serializer = self.get_serializer(leads, many=True)
        return Response(serializer.data)