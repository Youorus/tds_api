from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_date

from .models import JuristAppointment
from .serializers import (
    JuristAppointmentSerializer,
    JuristAppointmentCreateSerializer,
    JuristSerializer
)
from api.leads.models import Lead
from django.contrib.auth import get_user_model

from ..utils.email.appointments import (
    send_jurist_appointment_email,
    send_jurist_appointment_deleted_email,
)
from ..utils.jurist_slots import is_valid_day, get_available_slots_for_jurist

User = get_user_model()

class JuristAppointmentViewSet(viewsets.ModelViewSet):
    queryset = JuristAppointment.objects.all().select_related("jurist", "lead")
    serializer_class = JuristAppointmentSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['lead__id', 'date']

    def perform_create(self, serializer):
        instance = serializer.save()
        send_jurist_appointment_email(instance)

    def perform_destroy(self, instance):
        lead = instance.lead
        jurist = instance.jurist
        appointment_date = instance.date
        instance.delete()
        send_jurist_appointment_deleted_email(lead, jurist, appointment_date)

    def get_queryset(self):
        queryset = super().get_queryset()
        lead = self.request.query_params.get("lead")
        date = self.request.query_params.get("date")
        if lead and date:
            queryset = queryset.filter(lead_id=lead, date__date=date)
        elif lead:
            queryset = queryset.filter(lead_id=lead)
        elif date:
            queryset = queryset.filter(date__date=date)
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return JuristAppointmentCreateSerializer
        return JuristAppointmentSerializer

    @action(detail=False, methods=["get"])
    def available_jurists(self, request):
        """
        Retourne la liste des juristes dispos pour un lead et une date donnée.
        - Si le lead a déjà un juriste assigné, retourne uniquement celui-ci si dispo.
        - Sinon, retourne tous les juristes dispos pour cette date.
        """
        lead_id = request.query_params.get("lead_id")
        date_str = request.query_params.get("date")
        if not lead_id or not date_str:
            return Response({"detail": "lead_id et date requis."}, status=400)

        lead = Lead.objects.filter(id=lead_id).first()
        if not lead:
            return Response({"detail": "Lead introuvable."}, status=404)

        day = parse_date(date_str)
        if not day or not is_valid_day(day):
            return Response({"detail": "Date invalide (mardi/jeudi uniquement)."}, status=400)

        jurist_assigned = getattr(lead, "jurists_assigned", None)
        if jurist_assigned:
            # S'il y a bien un juriste assigné, on vérifie s'il est dispo
            slots = get_available_slots_for_jurist(jurist_assigned, day)
            if slots:
                serializer = JuristSerializer(jurist_assigned)
                return Response([serializer.data])
            else:
                return Response([])

        # Sinon, tous les juristes dispo à cette date
        jurists = User.objects.filter(role="JURISTE", is_active=True)
        available = [j for j in jurists if get_available_slots_for_jurist(j, day)]
        serializer = JuristSerializer(available, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def jurist_slots(self, request):
        """
        Liste les créneaux disponibles pour un juriste donné à une date donnée.
        """
        jurist_id = request.query_params.get("jurist_id")
        date_str = request.query_params.get("date")
        # Protection contre None/"None"/""
        if not jurist_id or jurist_id in ("None", "") or not date_str:
            return Response({"detail": "jurist_id et date requis."}, status=400)

        jurist = User.objects.filter(id=jurist_id, role="JURISTE", is_active=True).first()
        if not jurist:
            return Response({"detail": "Juriste introuvable."}, status=404)

        day = parse_date(date_str)
        if not day or not is_valid_day(day):
            return Response({"detail": "Date invalide (mardi/jeudi uniquement)."}, status=400)

        slots = get_available_slots_for_jurist(jurist, day)
        return Response(slots)

    @action(detail=False, methods=["get"])
    def upcoming_for_lead(self, request):
        lead_id = request.query_params.get("lead_id")
        if not lead_id:
            return Response({"detail": "lead_id requis."}, status=400)
        now = timezone.now()
        appointments = self.get_queryset().filter(
            lead_id=lead_id,
            date__gte=now
        ).order_by("date")
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)