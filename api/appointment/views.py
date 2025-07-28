# api/appointment/views.py

from datetime import datetime
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models.functions import TruncDate
from django.db.models import Count

from api.appointment.models import Appointment
from api.jurist_appointment.models import JuristAppointment
from api.appointment.serializers import AppointmentSerializer
from api.jurist_appointment.serializers import JuristAppointmentSerializer
from api.leads.models import Lead
from api.users.models import UserRoles  # <-- adapte si besoin

from api.utils.email.appointments import (
    send_appointment_created_or_updated_email,
    send_appointment_deleted_email,
)

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.select_related("lead", "created_by")
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.role in [UserRoles.ADMIN, UserRoles.ACCUEIL]:
            return qs
        elif user.role == UserRoles.CONSEILLER:
            return qs.filter(lead__assigned_to=user)
        elif user.role == UserRoles.JURISTE:
            # Option : afficher les RDV classiques des leads dont le juriste a au moins un RDV, sinon retourne qs.none()
            lead_ids = JuristAppointment.objects.filter(jurist=user).values_list("lead_id", flat=True)
            return qs.filter(lead_id__in=lead_ids)
        else:
            return qs.none()

    def perform_create(self, serializer):
        instance = serializer.save()
        send_appointment_created_or_updated_email(instance.lead, instance.date, is_update=False)
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        send_appointment_created_or_updated_email(instance.lead, instance.date, is_update=True)
        return instance

    def perform_destroy(self, instance):
        lead = instance.lead
        appointment_date = instance.date
        instance.delete()
        send_appointment_deleted_email(lead, appointment_date)

    @action(detail=False, methods=["get"], url_path="all-by-date")
    def all_by_date(self, request):
        """
        GET /appointments/all-by-date/?date=YYYY-MM-DD
        Retourne tous les rendez-vous (classiques + juristes) pour une date donnée,
        filtrés selon les droits de l'utilisateur connecté.
        """
        user = request.user
        date_str = request.query_params.get("date")
        if not date_str:
            return Response({"error": "Paramètre 'date' requis, format YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Format de date invalide, attendu YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)

        # RDV classiques
        appointments_qs = self.get_queryset().filter(date__date=day)
        appointments_data = AppointmentSerializer(appointments_qs, many=True).data

        # RDV juristes
        jurist_qs = JuristAppointment.objects.filter(date__date=day)
        if user.role in [UserRoles.ADMIN, UserRoles.ACCUEIL]:
            pass  # tous
        elif user.role == UserRoles.CONSEILLER:
            jurist_qs = jurist_qs.filter(lead__assigned_to=user)
        elif user.role == UserRoles.JURISTE:
            jurist_qs = jurist_qs.filter(jurist=user)
        else:
            jurist_qs = jurist_qs.none()

        jurist_appointments_data = JuristAppointmentSerializer(jurist_qs, many=True).data

        return Response({
            "appointments": appointments_data,
            "jurist_appointments": jurist_appointments_data,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="count-by-date")
    def count_by_date(self, request):
        """
        GET /appointments/count-by-date/
        Retourne un dict {date_str: count} du nombre total de rendez-vous par jour,
        filtré selon l'utilisateur connecté.
        """
        user = request.user

        # Filtre le queryset selon l'utilisateur
        appointments_qs = self.get_queryset()
        counts_appointment = (
            appointments_qs
            .annotate(day=TruncDate("date"))
            .values("day")
            .annotate(count=Count("id"))
        )

        jurist_qs = JuristAppointment.objects.all()
        if user.role in [UserRoles.ADMIN, UserRoles.ACCUEIL]:
            pass
        elif user.role == UserRoles.CONSEILLER:
            jurist_qs = jurist_qs.filter(lead__assigned_to=user)
        elif user.role == UserRoles.JURISTE:
            jurist_qs = jurist_qs.filter(jurist=user)
        else:
            jurist_qs = jurist_qs.none()

        counts_jurist = (
            jurist_qs
            .annotate(day=TruncDate("date"))
            .values("day")
            .annotate(count=Count("id"))
        )

        total_counts = {}
        for item in counts_appointment:
            total_counts[item["day"].isoformat()] = item["count"]
        for item in counts_jurist:
            day = item["day"].isoformat()
            if day in total_counts:
                total_counts[day] += item["count"]
            else:
                total_counts[day] = item["count"]

        return Response(total_counts, status=status.HTTP_200_OK)