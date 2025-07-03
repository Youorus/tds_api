from datetime import datetime

from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Q

from api.models import Lead, LeadStatus, User
from api.serializers.lead_serializers import LeadSerializer
from api.serializers.lead_status import LeadStatusUpdateSerializer
from api.services import NotificationService


class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]
    notification_service = NotificationService()

    from django.db.models import Q
    from django.utils.dateparse import parse_date

    from django.db.models import Q
    from api.models import LeadStatus

    def get_queryset(self):
        user = self.request.user
        queryset = Lead.objects.all()

        # 🔍 Recherche prioritaire
        search = self.request.query_params.get("search")
        if search:
            return queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            ).order_by("-created_at")

        # Restriction spécifique CONSEILLER
        if user.role == user.Roles.CONSEILLER:
            # On va chercher l'ID du statut "PRESENT" dynamiquement
            try:
                status_present = LeadStatus.objects.get(code="PRESENT")
                status_present_id = status_present.id
            except LeadStatus.DoesNotExist:
                # Si inexistant en base, on n'affiche QUE les leads assignés
                status_present_id = None

            # Filtrage combiné
            if status_present_id:
                queryset = queryset.filter(
                    Q(assigned_to=user)
                    | (Q(assigned_to__isnull=True) & Q(status_id=status_present_id))
                )
            else:
                queryset = queryset.filter(assigned_to=user)

        # --- Filtrage par statut (par ID) ---
        status_param = self.request.query_params.get("status")
        if status_param and status_param.upper() != "TOUS":
            queryset = queryset.filter(status_id=status_param)

        # --- Filtrage par date dynamique (created_at ou appointment_date) ---
        date_str = self.request.query_params.get("date")
        date_field = self.request.query_params.get("date_field", "created_at")
        if date_str:
            parsed_date = parse_date(date_str)
            if parsed_date:
                if date_field in ["created_at", "appointment_date"]:
                    filter_kwargs = {f"{date_field}__date": parsed_date}
                    queryset = queryset.filter(**filter_kwargs)
                else:
                    queryset = queryset.filter(created_at__date=parsed_date)

        return queryset.order_by("-created_at")

    @action(detail=False, methods=["get"], url_path="count-by-status")
    def count_by_status(self, request):
        status_codes = ["RDV_CONFIRME", "RDV_PLANIFIE", "ABSENT"]
        statuses = LeadStatus.objects.filter(code__in=status_codes)
        code_to_id = {status.code: status.id for status in statuses}
        today = timezone.localdate()  # YYYY-MM-DD

        results = {}

        # RDV_CONFIRMÉ : total (sans filtre date)
        status_id = code_to_id.get("RDV_CONFIRME")
        results["RDV_CONFIRME"] = Lead.objects.filter(status_id=status_id).count() if status_id else 0

        # RDV_PLANIFIÉ : total (sans filtre date)
        status_id = code_to_id.get("RDV_PLANIFIE")
        results["RDV_PLANIFIE"] = Lead.objects.filter(status_id=status_id).count() if status_id else 0

        # ABSENT : seulement aujourd’hui
        status_id = code_to_id.get("ABSENT")
        results["ABSENT"] = (
            Lead.objects.filter(status_id=status_id).count() if status_id else 0
        )

        return Response(results)

    def get_permissions(self):
        if self.action in ["create", "approve_assignment"]:
            return [AllowAny()]
        return super().get_permissions()

    def perform_create(self, serializer):
        # Met le statut RDV_PLANIFIE si non fourni
        data = serializer.validated_data
        lead_status = data.get("status")

        if not lead_status:
            try:
                default_status = LeadStatus.objects.get(code="RDV_PLANIFIE")
            except LeadStatus.DoesNotExist:
                raise Exception("Le statut 'RDV_PLANIFIE' n'existe pas en base !")
            serializer.save(status=default_status)
        else:
            serializer.save()

        lead = serializer.instance
        self.handle_lead_notification(lead)

    def handle_lead_notification(self, lead):
        status_code = getattr(lead.status, "code", None)
        if status_code == "RDV_CONFIRME":
            self.notification_service.send_appointment_confirmation(lead)
        elif status_code == "RDV_PLANIFIE":
            self.notification_service.send_appointment_planned(lead)

    def perform_update(self, serializer ):
        lead_before = self.get_object()
        appointment_before = lead_before.appointment_date
        status_before = getattr(lead_before.status, "code", None)

        lead = serializer.save()
        appointment_after = lead.appointment_date
        status_after = getattr(lead.status, "code", None)

        # 1. Cas 1 : La date de RDV a changé ET l'email existe
        if appointment_after and lead.email and appointment_before != appointment_after:
            # Envoie le mail du statut courant !
            if status_after == "RDV_CONFIRME":
                self.notification_service.send_appointment_confirmation(lead)
            if status_after == "RDV_PLANIFIE":
                self.notification_service.send_appointment_planned(lead)
            # (tu peux ajouter d'autres cas ici)

        # 2. Cas 2 : Le statut change (ex : RDV_CONFIRME <-> RDV_PLANIFIE)
        elif status_before != status_after and lead.email:
            if status_after == "RDV_PLANIFIE":
                self.notification_service.send_appointment_planned(lead)
            # (autres cas si besoin)



    @action(detail=True, methods=["patch"], url_path="assign")
    def assign_to_me(self, request, pk=None):
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
    def unassign_lead(self, request, pk=None):
        user = request.user
        lead = self.get_object()

        # Est-ce un admin ?
        is_admin = user.is_superuser or getattr(user, "role", None) == user.Roles.ADMIN

        # Si ce n'est ni l'admin ni l'utilisateur assigné → refus
        if not is_admin and lead.assigned_to != user:
            return Response(
                {"detail": "Seul un administrateur ou l'utilisateur assigné peut désassigner ce lead."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not lead.assigned_to:
            return Response(
                {"detail": "Ce lead n'est pas assigné."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # On désassigne
        lead.assigned_to = None
        lead.save()
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="request-assignment")
    def request_assignment(self, request, pk=None):
        user = request.user

        if user.role != User.Roles.CONSEILLER:
            return Response({"detail": "Seuls les conseillers peuvent faire une demande."}, status=403)

        try:
            lead = Lead.objects.get(pk=pk)
        except Lead.DoesNotExist:
            return Response({"detail": "Lead introuvable."}, status=404)

        self.notification_service.send_lead_assignment_request_to_admin(
            conseiller=user,
            lead=lead
        )
        return Response({"detail": "Demande d’assignation envoyée à l’administrateur."}, status=201)

