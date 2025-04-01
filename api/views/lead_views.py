from django.utils.timezone import now,timedelta
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.models import Lead, LeadStatus
from api.serializers import LeadSerializer


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [permissions.AllowAny]  # 👈 Ici on autorise tout

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        print(request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
        leads = Lead.objects.filter(status="rdv_confirme", appointment_date__lt=limite)
        updated = leads.update(status="absent")
        return Response({"message": f"{updated} leads mis à jour en 'absent'"})