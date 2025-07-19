# api/leads/views.py

from django.utils.dateparse import parse_date
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied

from api.lead_status.models import LeadStatus
from api.leads.models import Lead
from api.leads.serializers import LeadSerializer
from api.leads.constants import RDV_CONFIRME, RDV_PLANIFIE, ABSENT, PRESENT
from api.leads.permissions import IsLeadCreator, IsConseillerOrAdmin
from api.users.models import User
from api.users.roles import UserRoles
from api.utils.email.notifications import NotificationService

class LeadViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal pour la gestion CRUD des Leads.
    - Création : ADMIN, ACCUEIL (sauf /public-create/)
    - Modification/suppression/lecture : tout utilisateur connecté
    - Assignation : ADMIN ou CONSEILLER
    """
    serializer_class = LeadSerializer
    permission_classes = [IsLeadCreator]
    notification_service = NotificationService()

    def get_queryset(self):
        user = self.request.user
        queryset = Lead.objects.all()

        # Recherche plein texte
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )

        # Restriction CONSEILLER : uniquement ses leads OU ceux en statut PRESENT et non assignés
        if getattr(user, "role", None) == UserRoles.CONSEILLER:
            try:
                status_present = LeadStatus.objects.get(code=PRESENT)
                queryset = queryset.filter(
                    Q(assigned_to=user) |
                    Q(assigned_to__isnull=True, status=status_present)
                )
            except LeadStatus.DoesNotExist:
                # fallback : uniquement ses leads
                queryset = queryset.filter(assigned_to=user)

        # Filtrage par statut (après restriction conseiller)
        status_param = self.request.query_params.get("status")
        if status_param and status_param.upper() != "TOUS":
            queryset = queryset.filter(status_id=status_param)

        # Filtrage par date
        date_str = self.request.query_params.get("date")
        date_field = self.request.query_params.get("date_field", "created_at")
        if date_str:
            parsed_date = parse_date(date_str)
            if parsed_date and date_field in ["created_at", "appointment_date"]:
                queryset = queryset.filter(**{f"{date_field}__date": parsed_date})

        return queryset.order_by("-created_at")

    def get_permissions(self):
        # Route publique (accessible à tous)
        if self.action == "public_create":
            return [AllowAny()]
        # Assignation (patch/POST sur /assignment/, /request-assignment/)
        if self.action in ["assignment", "request_assignment"]:
            return [IsConseillerOrAdmin()]
        # Autres (utilise la permission globale)
        return super().get_permissions()

    def perform_create(self, serializer):
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
        status_code = getattr(lead.status, "code", None)
        print(f"[NOTIF] Statut du lead: {status_code}")
        if status_code == RDV_PLANIFIE:
            print(f"[NOTIF] Envoi du mail PLANIFIÉ à {lead.email} (lead id: {lead.id})")
            self.notification_service.send_appointment_planned(lead)
        elif status_code == RDV_CONFIRME:
            print(f"[NOTIF] Envoi du mail CONFIRMÉ à {lead.email} (lead id: {lead.id})")
            self.notification_service.send_appointment_confirmation(lead)
        else:
            print(f"[NOTIF] Aucun mail envoyé (statut={status_code}) pour {lead.email} (lead id: {lead.id})")

    def perform_update(self, serializer):
        lead_before = self.get_object()
        appointment_before = lead_before.appointment_date
        status_before = getattr(lead_before.status, "code", None)

        lead = serializer.save()
        appointment_after = lead.appointment_date
        status_after = getattr(lead.status, "code", None)

        if appointment_after and lead.email and appointment_before != appointment_after:
            if status_after == RDV_PLANIFIE:
                self.notification_service.send_appointment_planned(lead)
            elif status_after == RDV_CONFIRME:
                self.notification_service.send_appointment_confirmation(lead)
        elif status_before != status_after and lead.email:
            if status_after == RDV_PLANIFIE:
                self.notification_service.send_appointment_planned(lead)
            elif status_after == RDV_CONFIRME:
                self.notification_service.send_appointment_confirmation(lead)

    @action(detail=False, methods=["post"], url_path="public-create", permission_classes=[AllowAny])
    def public_create(self, request):
        """
        Route ouverte à tous pour créer un lead (landing page, prise de contact…).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lead = serializer.save()
        # Optionnel : notification, selon besoin
        return Response(self.get_serializer(lead).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="count-by-status")
    def count_by_status(self, request):
        statuses = LeadStatus.objects.filter(code__in=[RDV_CONFIRME, RDV_PLANIFIE, ABSENT])
        code_to_id = {status.code: status.id for status in statuses}
        results = {}
        for code in [RDV_CONFIRME, RDV_PLANIFIE, ABSENT]:
            status_id = code_to_id.get(code)
            results[code] = Lead.objects.filter(status_id=status_id).count() if status_id else 0
        return Response(results)

    @action(detail=True, methods=["patch"], url_path="assignment")
    def assignment(self, request, pk=None):
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

    @action(detail=True, methods=["post"], url_path="send-formulaire-email")
    def send_formulaire_email(self, request, pk=None):
        """
        Envoie au client le lien vers le formulaire de suivi personnalisé.
        """
        try:
            lead = self.get_object()
        except Lead.DoesNotExist:
            return Response({"detail": "Lead introuvable."}, status=status.HTTP_404_NOT_FOUND)

        # Appelle le service d'envoi
        self.notification_service.send_lead_formulaire(lead)
        return Response({"detail": "E-mail de formulaire envoyé."}, status=status.HTTP_200_OK)