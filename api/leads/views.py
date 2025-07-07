# leads/views.py

from django.utils.dateparse import parse_date
from django.db.models import Q
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from api.lead_status.models import LeadStatus
from api.leads.models import Lead
from api.leads.serializers import LeadSerializer
from api.leads.constants import RDV_CONFIRME, RDV_PLANIFIE, ABSENT, PRESENT
from api.leads.permissions import IsLeadEditor, IsConseillerOrAdmin
from api.users.models import User
from api.users.roles import UserRoles
from api.utils.email.notifications import NotificationService


class LeadViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal pour la gestion CRUD des Leads.
    Gère recherche, assignation, filtrage, notifications et restrictions fines par permission.
    """
    serializer_class = LeadSerializer
    permission_classes = [IsLeadEditor]
    notification_service = NotificationService()

    def get_queryset(self):
        """
        Retourne la liste filtrée des leads selon :
        - Recherche texte
        - Rôle (restriction conseiller)
        - Statut ou date
        """
        user = self.request.user
        queryset = Lead.objects.all()

        # --- Recherche plein texte (prénom, nom, email, phone) ---
        search = self.request.query_params.get("search")
        if search:
            return queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            ).order_by("-created_at")

        # --- Restriction CONSEILLER : accès à ses leads ou leads non assignés avec statut PRESENT ---
        if getattr(user, "role", None) == UserRoles.CONSEILLER:
            try:
                status_present = LeadStatus.objects.get(code=PRESENT)
                status_present_id = status_present.id
            except LeadStatus.DoesNotExist:
                status_present_id = None

            if status_present_id:
                queryset = queryset.filter(
                    Q(assigned_to=user)
                    | (Q(assigned_to__isnull=True) & Q(status_id=status_present_id))
                )
            else:
                queryset = queryset.filter(assigned_to=user)

        # --- Filtrage par statut (ID) ---
        status_param = self.request.query_params.get("status")
        if status_param and status_param.upper() != "TOUS":
            queryset = queryset.filter(status_id=status_param)

        # --- Filtrage par date (created_at/appointment_date) ---
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
        """
        Endpoint pour obtenir le nombre de leads par statut clé.
        (RDV_CONFIRME, RDV_PLANIFIE, ABSENT)
        """
        statuses = LeadStatus.objects.filter(code__in=[RDV_CONFIRME, RDV_PLANIFIE, ABSENT])
        code_to_id = {status.code: status.id for status in statuses}

        results = {}
        for code in [RDV_CONFIRME, RDV_PLANIFIE, ABSENT]:
            status_id = code_to_id.get(code)
            results[code] = Lead.objects.filter(status_id=status_id).count() if status_id else 0

        return Response(results)

    def get_permissions(self):
        """
        Permissions dynamiques :
        - Création (prise de RDV) : ouverte
        - Assignation : restreinte conseiller/admin
        - CRUD lead : permission par défaut
        """
        if self.action == "create":
            return [AllowAny()]
        if self.action in ["assignment", "request_assignment"]:
            return [IsConseillerOrAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """
        À la création :
        - Définit RDV_PLANIFIE si statut absent
        - Notifie le lead selon le statut choisi
        """
        data = serializer.validated_data
        lead_status = data.get("status")
        if not lead_status:
            try:
                default_status = LeadStatus.objects.get(code=RDV_PLANIFIE)
            except LeadStatus.DoesNotExist:
                raise NotFound("Le statut 'RDV_PLANIFIE' n'existe pas en base !")
            serializer.save(status=default_status)
        else:
            serializer.save()
        lead = serializer.instance
        self.handle_lead_notification(lead)

    def handle_lead_notification(self, lead):
        """
        Notification selon le statut du lead.
        """
        status_code = getattr(lead.status, "code", None)
        if status_code == RDV_CONFIRME:
            self.notification_service.send_appointment_confirmation(lead)
        elif status_code == RDV_PLANIFIE:
            self.notification_service.send_appointment_planned(lead)

    def perform_update(self, serializer):
        """
        Notifie sur changement de statut/date de RDV.
        """
        lead_before = self.get_object()
        appointment_before = lead_before.appointment_date
        status_before = getattr(lead_before.status, "code", None)

        lead = serializer.save()
        appointment_after = lead.appointment_date
        status_after = getattr(lead.status, "code", None)

        # Notifie si la date de RDV a changé
        if appointment_after and lead.email and appointment_before != appointment_after:
            if status_after == RDV_CONFIRME:
                self.notification_service.send_appointment_confirmation(lead)
            if status_after == RDV_PLANIFIE:
                self.notification_service.send_appointment_planned(lead)

        # Notifie si le statut change
        elif status_before != status_after and lead.email:
            if status_after == RDV_PLANIFIE:
                self.notification_service.send_appointment_planned(lead)

    # ----------- ENDPOINT RESTFUL POUR ASSIGNATION -----------

    @action(detail=True, methods=["patch"], url_path="assignment")
    def assignment(self, request, pk=None):
        """
        PATCH /leads/{id}/assignment/
        - { assigned_to: <user_id> } => Assigne à l’utilisateur
        - { assigned_to: null }      => Désassignation
        - Seuls ADMIN/CONSEILLER peuvent s’auto-assigner ou se désassigner
        - Seul ADMIN peut assigner à quelqu’un d’autre
        """
        user = request.user
        lead = self.get_object()
        assigned_to_id = request.data.get("assigned_to", None)

        # Désassignation
        if assigned_to_id is None:
            if user.role not in [UserRoles.ADMIN, UserRoles.CONSEILLER]:
                raise PermissionDenied("Permission refusée pour désassigner ce lead.")
            if user.role == UserRoles.CONSEILLER and lead.assigned_to != user:
                raise PermissionDenied("Seul l’admin ou l’utilisateur assigné peut désassigner.")
            lead.assigned_to = None
            lead.save()
            return Response(status=status.HTTP_200_OK)

        # Assignation à un utilisateur
        try:
            assigned_user = User.objects.get(pk=assigned_to_id)
        except User.DoesNotExist:
            raise NotFound("Utilisateur introuvable.")

        if user.role == UserRoles.ADMIN or (user.role == UserRoles.CONSEILLER and user == assigned_user):
            lead.assigned_to = assigned_user
            lead.save()
            return Response(status=status.HTTP_200_OK)
        else:
            raise PermissionDenied("Permission refusée pour cette assignation.")

    @action(detail=True, methods=["post"], url_path="request-assignment")
    def request_assignment(self, request, pk=None):
        """
        Permet à un conseiller de demander l’assignation d’un lead à un admin.
        """
        user = request.user

        if user.role != UserRoles.CONSEILLER:
            raise PermissionDenied("Seuls les conseillers peuvent faire une demande.")

        try:
            lead = Lead.objects.get(pk=pk)
        except Lead.DoesNotExist:
            raise NotFound("Lead introuvable.")

        self.notification_service.send_lead_assignment_request_to_admin(
            conseiller=user,
            lead=lead
        )
        return Response({"detail": "Demande d’assignation envoyée à l’administrateur."}, status=201)