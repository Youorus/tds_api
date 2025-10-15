# api/leads/views.py

from django.db import transaction
from django.db.models import F, Q
from django.utils.dateparse import parse_date
from rest_framework import status as drf_status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.booking.models import SlotQuota
from api.lead_status.models import LeadStatus
from api.leads.constants import ABSENT, PRESENT, RDV_CONFIRME, RDV_PLANIFIE
from api.leads.models import Lead
from api.leads.permissions import IsConseillerOrAdmin, IsLeadCreator
from api.leads.serializers import LeadSerializer
from api.users.models import User
from api.users.roles import UserRoles
from api.utils.email.leads.tasks import (
    send_appointment_confirmation_task,
    send_appointment_planned_task,
    send_dossier_status_notification_task,
    send_formulaire_task,
    send_jurist_assigned_notification_task
)

"""
Vues pour la gestion des Leads via API REST.

Ce module contient le `LeadViewSet`, qui permet :
- la création, lecture, mise à jour et suppression de leads (CRUD)
- des actions personnalisées (assignation de conseiller/juriste, création publique, etc.)
- l’envoi de notifications email selon les statuts et événements

Chaque action respecte les permissions associées au rôle utilisateur.
"""


class LeadViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal pour la gestion des leads.

    Fonctionnalités :
    - CRUD classique
    - Assignation des conseillers ou juristes
    - Création publique avec gestion de quota horaire
    - Envoi automatique de notifications email selon le statut ou la modification
    - Filtres dynamiques sur la date, le statut, le texte

    Permissions :
    - Créateur du lead (IsLeadCreator) par défaut
    - Public (AllowAny) pour la création publique
    - Admin ou Conseiller requis pour l’assignation
    """

    serializer_class = LeadSerializer
    permission_classes = [IsLeadCreator]

    def get_queryset(self):
        user = self.request.user
        queryset = Lead.objects.all()

        # ⚡️ Pas de filtrage par rôle → tout le monde voit le même jeu de données
        queryset = self._filter_by_search(queryset)
        queryset = self._filter_by_status(queryset)
        queryset = self._filter_by_date(queryset)

        return queryset.order_by("-created_at")

    # ==== FILTRES ====

    def _filter_by_search(self, queryset):
        search = self.request.query_params.get("search")
        if search:
            return queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
                | Q(email__icontains=search)
            )
        return queryset

    def _filter_by_status(self, queryset):
        status_param = self.request.query_params.get("status")
        if status_param and status_param.upper() != "TOUS":
            return queryset.filter(status_id=status_param)
        return queryset

    def _filter_by_date(self, queryset):
        date_str = self.request.query_params.get("date")
        date_field = self.request.query_params.get("date_field", "created_at")
        if date_str:
            parsed_date = parse_date(date_str)
            if parsed_date and date_field in ["created_at", "appointment_date"]:
                return queryset.filter(**{f"{date_field}__date": parsed_date})
        return queryset

    # ==== PERMISSIONS ====

    def get_permissions(self):
        if self.action == "public_create":
            return [AllowAny()]
        if self.action in ["assignment", "request_assignment"]:
            return [IsConseillerOrAdmin()]
        return super().get_permissions()

    # ==== CREATE & UPDATE ====

    def perform_create(self, serializer):
        lead_status = serializer.validated_data.get("status")
        if not lead_status:
            lead_status = self._get_default_status()

        lead = serializer.save(status=lead_status)
        self._send_notifications(lead)

    def _get_default_status(self):
        try:
            return LeadStatus.objects.get(code=RDV_PLANIFIE)
        except LeadStatus.DoesNotExist:
            raise NotFound("Le statut 'RDV_PLANIFIE' n'existe pas en base.")

    def _send_notifications(self, lead):
        code = getattr(lead.status, "code", None)
        if not lead.email:
            return

        if code == RDV_PLANIFIE:
            send_appointment_planned_task.delay(lead.id)
        elif code == RDV_CONFIRME:
            send_appointment_confirmation_task.delay(lead.id)

    def perform_update(self, serializer):
        lead_before = self.get_object()
        lead_after = serializer.save()

        self._handle_update_notifications(lead_before, lead_after)

    def _handle_update_notifications(self, before, after):
        if not after.email:
            return

        status_changed = getattr(before.status, "code", None) != getattr(
            after.status, "code", None
        )
        appointment_changed = before.appointment_date != after.appointment_date
        statut_dossier_changed = getattr(before.statut_dossier, "id", None) != getattr(
            after.statut_dossier, "id", None
        )

        if appointment_changed:
            self._send_notifications(after)
        elif status_changed:
            self._send_notifications(after)

        if statut_dossier_changed and after.statut_dossier:
            send_dossier_status_notification_task.delay(after.id)

    # ====== ROUTES PERSONNALISÉES ======

    @action(
        detail=False,
        methods=["post"],
        url_path="public-create",
        permission_classes=[AllowAny],
    )
    def public_create(self, request):
        """
        Crée un lead via un formulaire public (sans authentification).

        Valide que le créneau horaire est disponible.
        Réserve dynamiquement un slot (`SlotQuota`) si disponible.
        Envoie un email selon le statut choisi (RDV_PLANIFIE ou RDV_CONFIRME).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        appt_dt = serializer.validated_data.get("appointment_date")
        if not appt_dt:
            raise ValidationError({"appointment_date": "Champ requis."})

        with transaction.atomic():
            quota, _ = SlotQuota.objects.get_or_create(
                start_at=appt_dt,
                defaults={"capacity": 1, "booked": 0},
            )

            updated = SlotQuota.objects.filter(
                pk=quota.pk, booked__lt=F("capacity")
            ).update(booked=F("booked") + 1)

            if updated == 0:
                return Response(
                    {"detail": "Créneau complet. Veuillez choisir un autre horaire."},
                    status=drf_status.HTTP_409_CONFLICT,
                )

            lead_status = (
                serializer.validated_data.get("status") or self._get_default_status()
            )
            lead = serializer.save(status=lead_status)

        self._send_notifications(lead)
        return Response(
            self.get_serializer(lead).data, status=drf_status.HTTP_201_CREATED
        )

    @action(detail=False, methods=["get"], url_path="count-by-status")
    def count_by_status(self, request):
        """
        Retourne un comptage des leads par statut :
        - RDV_CONFIRME
        - RDV_PLANIFIE
        - ABSENT

        Utilisé pour le dashboard de statistiques.
        """
        statuses = LeadStatus.objects.filter(
            code__in=[RDV_CONFIRME, RDV_PLANIFIE, ABSENT]
        )
        counts = {
            code: (
                Lead.objects.filter(status=status).count()
                if (status := statuses.filter(code=code).first())
                else 0
            )
            for code in [RDV_CONFIRME, RDV_PLANIFIE, ABSENT]
        }
        return Response(counts)

    @action(detail=True, methods=["patch"], url_path="assignment")
    def assignment(self, request, pk=None):
        """
        Assigne ou désassigne un ou plusieurs conseillers à un lead.

        - ADMIN : peut assigner ou désassigner n’importe quel conseiller.
        - CONSEILLER : peut uniquement s’auto-assigner ou se désassigner.
        """
        lead = self.get_object()
        user = request.user

        if user.role == UserRoles.ADMIN:
            assign_ids = request.data.get("assign", [])
            unassign_ids = request.data.get("unassign", [])

            if assign_ids:
                valid_users = User.objects.filter(
                    id__in=assign_ids, role=UserRoles.CONSEILLER, is_active=True
                )
                if valid_users.count() != len(assign_ids):
                    raise NotFound("Un ou plusieurs conseillers sont introuvables.")
                lead.assigned_to.add(*valid_users)

            if unassign_ids:
                users_to_unassign = User.objects.filter(
                    id__in=unassign_ids, role=UserRoles.CONSEILLER
                )
                lead.assigned_to.remove(*users_to_unassign)

        elif user.role == UserRoles.CONSEILLER:
            action = request.data.get("action")
            if action not in ["assign", "unassign"]:
                return Response(
                    {"detail": "Action attendue : 'assign' ou 'unassign'."}, status=400
                )

            if action == "assign" and not lead.assigned_to.filter(id=user.id).exists():
                lead.assigned_to.add(user)
            elif action == "unassign" and lead.assigned_to.filter(id=user.id).exists():
                lead.assigned_to.remove(user)
        else:
            raise PermissionDenied(
                "Seuls les admins ou conseillers peuvent gérer les assignations."
            )

        lead.save()
        return Response(self.get_serializer(lead).data)

    @action(detail=True, methods=["patch"], url_path="assign-juristes")
    def assign_juristes(self, request, pk=None):
        """
        Assigne ou désassigne un ou plusieurs juristes à un lead (ADMIN uniquement).
        """
        user = request.user
        if user.role != UserRoles.ADMIN:
            raise PermissionDenied("Seul un admin peut gérer les juristes assignés.")

        lead = self.get_object()
        assign_ids = request.data.get("assign", [])
        unassign_ids = request.data.get("unassign", [])

        if assign_ids:
            juristes = User.objects.filter(
                id__in=assign_ids, role=UserRoles.JURISTE, is_active=True
            )
            if juristes.count() != len(assign_ids):
                raise NotFound("Un ou plusieurs juristes à assigner sont introuvables.")
            lead.jurist_assigned.add(*juristes)

            if lead.email and juristes.exists():
                main_jurist = juristes.first()
                send_jurist_assigned_notification_task.delay(lead.id, main_jurist.id)

        if unassign_ids:
            juristes = User.objects.filter(id__in=unassign_ids, role=UserRoles.JURISTE)
            lead.jurist_assigned.remove(*juristes)

        lead.save()
        return Response(self.get_serializer(lead).data)

    @action(detail=True, methods=["post"], url_path="send-formulaire-email")
    def send_formulaire_email(self, request, pk=None):
        """
        Déclenche l’envoi d’un e-mail contenant le formulaire au lead concerné.
        """
        lead = self.get_object()
        send_formulaire_task.delay(lead.id)
        return Response({"detail": "E-mail de formulaire envoyé."}, status=200)
