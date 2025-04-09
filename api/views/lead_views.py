from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils.timezone import now
from datetime import timedelta

from api.models import Lead, LeadStatus
from api.serializers import LeadSerializer, LeadStatusUpdateSerializer
from api.services import NotificationService


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Initialisation du service de notification
    notification_service = NotificationService()

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        lead = serializer.save()
        print(lead)
        if lead.appointment_date and lead.email:
            self.notification_service.send_appointment_confirmation(lead)
        elif not lead.appointment_date and lead.email:
            self.notification_service.send_welcome(lead)

    def perform_update(self, serializer):
        lead_before = self.get_object()
        appointment_before = lead_before.appointment_date
        status_before = lead_before.status

        lead = serializer.save()
        appointment_after = lead.appointment_date
        status_after = lead.status

        if appointment_after and lead.email and appointment_before != appointment_after:
            self.notification_service.send_appointment_confirmation(lead)

        # Envoie une notification si le statut vient de passer à ABSENT
        if status_before != LeadStatus.ABSENT and status_after == LeadStatus.ABSENT:
            self.notification_service.send_missed_appointment(lead)

    @action(detail=True, methods=["patch"], url_path="set-status")
    def set_status(self, request, pk=None):
        lead = self.get_object()
        serializer = LeadStatusUpdateSerializer(lead, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        status_before = lead.status
        lead = serializer.save()

        if status_before != LeadStatus.ABSENT and lead.status == LeadStatus.ABSENT:
            self.notification_service.send_missed_appointment(lead)

        return Response({"status": serializer.data["status"]}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="statut-nouveau")
    def get_nouveaux_leads(self, request):
        count = Lead.objects.filter(status=LeadStatus.NOUVEAU).count()
        return Response({"count": count})

    @action(detail=False, methods=["get"], url_path="rdv-demain")
    def get_leads_rdv_demain(self, request):
        tomorrow = now().date() + timedelta(days=1)
        leads = Lead.objects.filter(appointment_date__date=tomorrow)
        for lead in leads:
            # Utilisation du service unifié pour les rappels
            self.notification_service.send_appointment_reminder(lead)
        return Response({"count": leads.count()})

    @action(detail=False, methods=["get"], url_path="statut-absent")
    def get_leads_absents(self, request):
        count = Lead.objects.filter(status=LeadStatus.ABSENT).count()
        return Response({"count": count})

    @action(detail=False, methods=["post"], url_path="maj-absents-auto")
    def maj_leads_absents_auto(self, request):
        limite = now() - timedelta(hours=1)
        leads = Lead.objects.filter(status=LeadStatus.RDV_CONFIRME, appointment_date__lt=limite)
        updated_count = 0
        for lead in leads:
            lead.status = LeadStatus.ABSENT
            lead.save()
            self.notification_service.send_missed_appointment(lead)
            updated_count += 1

        return Response({"message": f"{updated_count} leads mis à jour en 'absent'"})


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