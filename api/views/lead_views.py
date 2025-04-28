from django.utils.dateparse import parse_date
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from api.models import Lead, LeadStatus, User
from api.serializers import LeadSerializer, LeadStatusUpdateSerializer
from api.services import NotificationService


class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]

    notification_service = NotificationService()

    def get_queryset(self):
        user = self.request.user
        queryset = Lead.objects.all()

        # 🔐 Restriction d'accès en fonction du rôle
        if not (user.is_superuser or user.role in [User.Roles.ADMIN, User.Roles.ACCUEIL]):
            if user.role == User.Roles.CONSEILLER:
                queryset = queryset.filter(Q(assigned_to=user) | Q(assigned_to__isnull=True))
            else:
                queryset = queryset.filter(assigned_to=user)

        # ✅ Filtrage par statut
        status_param = self.request.query_params.get("status")
        if status_param and status_param.upper() != "TOUS":
            queryset = queryset.filter(status__iexact=status_param)

        # ✅ Filtrage par date
        date_str = self.request.query_params.get("date")
        if date_str:
            parsed_date = parse_date(date_str)
            if parsed_date:
                queryset = queryset.filter(created_at__date=parsed_date)

        # ✅ Recherche textuelle
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )

        return queryset.order_by("-created_at")

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        lead = serializer.save()
        if lead.appointment_date and lead.email:
            self.notification_service.send_appointment_confirmation(lead)
        elif lead.email:
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
