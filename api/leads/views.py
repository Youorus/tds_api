# api/leads/views.py
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework import status as drf_status

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

        # 🔸 Restriction JURISTE : uniquement les leads qui lui sont assignés
        if getattr(user, "role", None) == UserRoles.JURISTE:
            queryset = queryset.filter(jurist_assigned=user)

        # 🔸 Recherche plein texte
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )

        # 🔸 Restriction CONSEILLER : ses leads OU leads non assignés avec statut PRÉSENT
        if getattr(user, "role", None) == UserRoles.CONSEILLER:
            try:
                status_present = LeadStatus.objects.get(code=PRESENT)
                queryset = queryset.filter(
                    Q(assigned_to=user) |
                    Q(assigned_to__isnull=True, status=status_present)
                )
            except LeadStatus.DoesNotExist:
                queryset = queryset.filter(assigned_to=user)

        # 🔸 Filtrage par statut
        status_param = self.request.query_params.get("status")
        if status_param and status_param.upper() != "TOUS":
            queryset = queryset.filter(status_id=status_param)

        # 🔸 Filtrage par date
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
        print("=== RAW DATA REÇUE ===", self.request.data)

        data = serializer.validated_data
        status_param = self.request.query_params.get("status")
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
        statut_dossier_before = getattr(lead_before.statut_dossier, "id", None)  # <-- Ajout

        lead = serializer.save()
        appointment_after = lead.appointment_date


        print(appointment_before)
        print(appointment_after)

        status_after = getattr(lead.status, "code", None)
        statut_dossier_after = getattr(lead.statut_dossier, "id", None)  # <-- Ajout

        # Notification RDV
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

        # ====== Notification statut dossier ======
        if statut_dossier_before != statut_dossier_after and lead.statut_dossier and lead.email:
            self.notification_service.send_dossier_status_notification(lead)

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


    @action(detail=True, methods=["patch"], url_path="assign-juristes")
    def assign_juristes(self, request, pk=None):
            """
            ADMIN ONLY : Assigne ou désassigne un ou plusieurs juristes sur un lead.
            Payload :
            {
                "assign": [<user_id>, ...],   # IDs à assigner
                "unassign": [<user_id>, ...]  # IDs à désassigner
            }
            """
            user = request.user
            if getattr(user, "role", None) != UserRoles.ADMIN:
                raise PermissionDenied("Seul un admin peut gérer les juristes assignés.")

            lead = self.get_object()
            assign_ids = request.data.get("assign", [])
            unassign_ids = request.data.get("unassign", [])

            # Assignation
            if assign_ids:
                juristes_to_assign = User.objects.filter(id__in=assign_ids, role=UserRoles.JURISTE, is_active=True)
                if juristes_to_assign.count() != len(assign_ids):
                    raise NotFound("Un ou plusieurs juristes à assigner sont introuvables ou inactifs.")
                lead.jurist_assigned.add(*juristes_to_assign)

            # Désassignation
            if unassign_ids:
                juristes_to_unassign = User.objects.filter(id__in=unassign_ids, role=UserRoles.JURISTE)
                lead.jurist_assigned.remove(*juristes_to_unassign)

            lead.save()
            serializer = self.get_serializer(lead)
            return Response(serializer.data, status=200)

    @action(detail=True, methods=["patch"], url_path="assignment")
    def assignment(self, request, pk=None):
        """
        - ADMIN : assignation/désassignation de conseillers (payload : {"assign": [ids]} ou {"unassign": [ids]})
        - CONSEILLER : auto-assignation/désassignation (payload : {"action": "assign"} ou {"action": "unassign"})
        """
        user = request.user
        lead = self.get_object()
        print("=== PAYLOAD RECU ===", dict(request.data))
        print("ROLE UTILISATEUR :", user.role)

        if user.role == UserRoles.ADMIN:
            assign_ids = request.data.get("assign", [])
            unassign_ids = request.data.get("unassign", [])

            if assign_ids:
                users_to_assign = User.objects.filter(id__in=assign_ids, role=UserRoles.CONSEILLER, is_active=True)
                if users_to_assign.count() != len(assign_ids):
                    raise NotFound("Un ou plusieurs conseillers à assigner sont introuvables ou inactifs.")
                lead.assigned_to.add(*users_to_assign)

            if unassign_ids:
                users_to_unassign = User.objects.filter(id__in=unassign_ids, role=UserRoles.CONSEILLER)
                lead.assigned_to.remove(*users_to_unassign)

            lead.save()
            serializer = self.get_serializer(lead)
            return Response(serializer.data, status=200)

        elif user.role == UserRoles.CONSEILLER:
            action_type = request.data.get("action")
            if action_type not in ["assign", "unassign"]:
                return Response({"detail": "Action attendue : 'assign' ou 'unassign'."}, status=400)

            if action_type == "assign":
                if not lead.assigned_to.filter(id=user.id).exists():
                    lead.assigned_to.add(user)
            elif action_type == "unassign":
                if lead.assigned_to.filter(id=user.id).exists():
                    lead.assigned_to.remove(user)

            lead.save()
            serializer = self.get_serializer(lead)
            return Response(serializer.data, status=200)

        else:
            raise PermissionDenied("Seuls les admins ou conseillers peuvent gérer l’assignation des leads.")

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
