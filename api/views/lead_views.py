import time

from django.utils.dateparse import parse_date
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Q
from rest_framework.request import Request

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

        # 🔍 Recherche textuelle = override tous les filtres
        search = self.request.query_params.get("search")
        if search:
            return queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            ).order_by("-created_at")

        # ✅ Si pas de recherche, on applique les filtres
        # 🔐 Restriction pour les conseillers
        if user.role == User.Roles.CONSEILLER:
            queryset = queryset.filter(
                Q(assigned_to__isnull=True) | Q(assigned_to=user)
            )

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

        return queryset.order_by("-created_at")

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        start = time.time()
        lead = serializer.save()
        # ...
        print("⏱️ Backend create duration:", time.time() - start, "seconds")

    #def perform_create(self, serializer):
        #lead = serializer.save()
        #if lead.appointment_date and lead.email:
           # self.notification_service.send_appointment_confirmation(lead)
       # elif lead.email:
         #   self.notification_service.send_welcome(lead)

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

    @action(detail=True, methods=["patch"], url_path="assign")
    def assign_to_me(self, request, pk=None):
        """
        Permet à l'utilisateur connecté de s'assigner ce lead
        uniquement s'il est CONSEILLER ou ADMIN.
        """
        user = request.user
        lead = self.get_object()

        if user.role not in [User.Roles.CONSEILLER, User.Roles.ADMIN]:
            return Response(
                {"detail": "Vous n'avez pas la permission de vous assigner ce lead."},
                status=status.HTTP_403_FORBIDDEN
            )

        lead.assigned_to = user
        lead.save()

        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"], url_path="unassign")
    def unassign_me(self, request, pk=None):
        """
        Permet à l'utilisateur connecté de se désassigner du lead.
        """
        user = request.user
        lead = self.get_object()

        # ✅ Vérifie si l'utilisateur est bien assigné à ce lead
        if lead.assigned_to != user:
            return Response(
                {"detail": "Vous n'êtes pas assigné à ce lead."},
                status=status.HTTP_403_FORBIDDEN
            )

        # ✅ Désassigner
        lead.assigned_to = None
        lead.save()

        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="request-assignment")
    def request_assignment(self, request, pk=None):
        user = request.user

        try:
            lead = Lead.objects.get(pk=pk)
        except Lead.DoesNotExist:
            return Response({"detail": "Lead introuvable."}, status=404)

        if user.role != User.Roles.CONSEILLER:
            return Response({"detail": "Seuls les conseillers peuvent faire une demande."}, status=403)

        self.notification_service.send_lead_assignment_request_to_admin(
            conseiller=user,
            lead=lead
        )
        return Response({"detail": "Demande d’assignation envoyée à l’administrateur."}, status=201)

    def get_permissions(self):
        if self.action == "approve_assignment":
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=["get"], url_path="approve-assignment")
    def approve_assignment(self, request):
        lead_id = request.query_params.get("lead_id")
        user_id = request.query_params.get("user_id")

        if not lead_id or not user_id:
            return Response(
                {"detail": "Paramètres requis manquants : lead_id et user_id."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lead = Lead.objects.get(pk=lead_id)
        except Lead.DoesNotExist:
            return Response({"detail": "Lead introuvable."}, status=status.HTTP_404_NOT_FOUND)

        try:
            conseiller = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "Conseiller introuvable."}, status=status.HTTP_404_NOT_FOUND)

        # 🔁 Réassigner même si déjà assigné à quelqu’un d’autre
        if lead.assigned_to and lead.assigned_to.id != conseiller.id:
            previous = lead.assigned_to.get_full_name()
            print(f"[INFO] Réassignation du lead {lead.id} de {previous} à {conseiller.get_full_name()}")

        lead.assigned_to = conseiller
        lead.save()

        self.notification_service.send_lead_assignment_confirmation_to_conseiller(
            conseiller=conseiller,
            lead=lead
        )

        return Response(
            {
                "detail": f"Le lead {lead.first_name} {lead.last_name} a bien été assigné à {conseiller.get_full_name()}."
            },
            status=status.HTTP_200_OK
        )