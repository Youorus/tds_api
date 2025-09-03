# api/leads/test_views.py
from datetime import date, datetime, time
from typing import Optional

from django.db.models import Exists, F, OuterRef
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import get_current_timezone, is_naive, make_aware
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.leads.models import Lead


def _parse_iso_any(dt: Optional[str]) -> Optional[object]:
    """
    Parse une chaîne ISO en datetime ou date, selon le format.

    Cette fonction tente d'interpréter une chaîne donnée comme un datetime ISO 8601 (ex: 'YYYY-MM-DDTHH:MM(:SS)') ou une date ISO (ex: 'YYYY-MM-DD').
    Si la chaîne est vide ou None, elle retourne None.
    Si le parsing échoue, elle retourne None.

    Retourne un objet datetime (naïf) si le format datetime est détecté, ou un objet date si le format date est détecté.
    """
    if not dt:
        return None
    return parse_datetime(dt) or parse_date(dt)


def _to_aware(
    dt_or_d: Optional[object], end_of_day: bool = False
) -> Optional[datetime]:
    """
    Convertit une date ou un datetime en datetime timezone-aware selon le fuseau horaire courant.

    - Si l'entrée est un objet date (sans heure), construit un datetime à minuit (00:00:00) ou à la fin de la journée (23:59:59.999999) si end_of_day=True.
    - Si l'entrée est un datetime naïf (sans information de fuseau), la rend aware avec le fuseau courant.
    - Si l'entrée est déjà un datetime aware, la retourne telle quelle.
    - Si l'entrée est None, retourne None.
    """
    if dt_or_d is None:
        return None

    tz = get_current_timezone()

    if isinstance(dt_or_d, date) and not isinstance(dt_or_d, datetime):
        if end_of_day:
            dt = datetime.combine(dt_or_d, time(23, 59, 59, 999999))
        else:
            dt = datetime.combine(dt_or_d, time(0, 0, 0, 0))
        return make_aware(dt, timezone=tz)

    dt = dt_or_d
    if is_naive(dt):
        return make_aware(dt, timezone=tz)
    return dt


def _normalize_avec_sans(value: Optional[str]) -> Optional[str]:
    """
    Normalise une chaîne en 'avec', 'sans' ou None.

    Reconnaît plusieurs variantes pour indiquer la présence ('avec', 'oui', 'with', 'true', '1') ou l'absence ('sans', 'non', 'without', 'false', '0').
    Si la valeur est None, vide ou ne correspond pas à ces variantes, retourne None.
    """
    if not value:
        return None
    v = value.strip().lower()
    if v in {"avec", "oui", "with", "true", "1"}:
        return "avec"
    if v in {"sans", "non", "without", "false", "0"}:
        return "sans"
    return None


def _to_int_or_none(val: Optional[str]) -> Optional[int]:
    """
    Tente de convertir une chaîne de caractères en entier.

    Si la conversion échoue (valeur invalide ou None), retourne None.
    """
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


class LeadSearchView(APIView):
    """
    Vue API permettant la recherche et la filtration des leads.

    Cette vue supporte plusieurs filtres sur les dates de création et de rendez-vous, les statuts (par code ou ID),
    la présence ou absence de juriste et conseiller, ainsi que la pagination et le tri des résultats.

    Filtres acceptés :
    - date_from, date_to : bornes sur la date de création des leads
    - appt_from, appt_to : bornes sur la date de rendez-vous
    - status_code, status_id : filtre sur le statut du lead
    - dossier_code, dossier_id : filtre sur le statut du dossier
    - has_jurist : 'avec' ou 'sans' pour filtrer selon la présence d'un juriste assigné
    - has_conseiller : 'avec' ou 'sans' pour filtrer selon la présence d'un conseiller assigné

    Pagination :
    - page : numéro de page (min 1, défaut 1)
    - page_size : nombre d'éléments par page (entre 1 et 200, défaut 20)

    Tri :
    - ordering : champ de tri parmi une liste blanche (par défaut '-created_at')

    La réponse contient le total des résultats, la page courante, la taille de page, le critère de tri et la liste des leads.
    """

    permission_classes = [IsAuthenticated]  # ajuste selon ton contexte

    def get(self, request):
        # --- Query params (bruts) ---
        raw_date_from = request.query_params.get("date_from")
        raw_date_to = request.query_params.get("date_to")
        raw_appt_from = request.query_params.get("appt_from")
        raw_appt_to = request.query_params.get("appt_to")

        # Filtres statut (code/ID)
        status_code = request.query_params.get("status_code")  # ex: "RDV_CONFIRME"
        status_id = _to_int_or_none(request.query_params.get("status_id"))
        dossier_code = request.query_params.get("dossier_code")  # ex: "A_TRAITER"
        dossier_id = _to_int_or_none(request.query_params.get("dossier_id"))

        # Filtres binaires
        has_jurist = _normalize_avec_sans(
            request.query_params.get("has_jurist")
        )  # 'avec'|'sans'|None
        has_conseille = _normalize_avec_sans(
            request.query_params.get("has_conseiller")
        )  # 'avec'|'sans'|None

        # Pagination / tri
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except Exception:
            page = 1
        try:
            page_size = min(max(int(request.query_params.get("page_size", 20)), 1), 200)
        except Exception:
            page_size = 20

        # Whitelist d’ordering
        allowed_ordering = {
            "created_at",
            "-created_at",
            "appointment_date",
            "-appointment_date",
            "id",
            "-id",
        }
        ordering = request.query_params.get("ordering", "-created_at")
        if ordering not in allowed_ordering:
            ordering = "-created_at"

        # --- Parse & normalize dates (timezone-aware) ---
        date_from_any = _parse_iso_any(raw_date_from)  # date ou datetime
        date_to_any = _parse_iso_any(raw_date_to)
        appt_from_any = _parse_iso_any(raw_appt_from)
        appt_to_any = _parse_iso_any(raw_appt_to)

        date_from = _to_aware(date_from_any, end_of_day=False)
        date_to = _to_aware(date_to_any, end_of_day=True)  # inclure toute la journée
        appt_from = _to_aware(appt_from_any, end_of_day=False)
        appt_to = _to_aware(appt_to_any, end_of_day=True)

        # --- Base queryset + annotations utiles ---
        ThroughConseiller = Lead.assigned_to.through
        ThroughJurist = Lead.jurist_assigned.through

        qs = Lead.objects.select_related("status", "statut_dossier").annotate(
            has_conseiller=Exists(
                ThroughConseiller.objects.filter(lead_id=OuterRef("pk"))
            ),
            has_jurist=Exists(ThroughJurist.objects.filter(lead_id=OuterRef("pk"))),
            # Statut lead
            lead_status_code=F("status__code"),
            lead_status_label=F("status__label"),
            lead_status_color=F("status__color"),
            # Statut dossier
            statut_dossier_code=F("statut_dossier__code"),
            statut_dossier_label=F("statut_dossier__label"),
            statut_dossier_color=F("statut_dossier__color"),
        )

        # --- Filtres de période (création) ---
        if date_from:
            qs = qs.filter(created_at__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)

        # --- Filtres de période (appointment) ---
        if appt_from:
            qs = qs.filter(
                appointment_date__isnull=False, appointment_date__gte=appt_from
            )
        if appt_to:
            qs = qs.filter(
                appointment_date__isnull=False, appointment_date__lte=appt_to
            )

        # --- Filtres métier ---
        # PRIORITÉ ID > code pour statuts
        if status_id is not None:
            qs = qs.filter(status_id=status_id)
        elif status_code:
            qs = qs.filter(status__code=status_code)

        if dossier_id is not None:
            qs = qs.filter(statut_dossier_id=dossier_id)
        elif dossier_code:
            qs = qs.filter(statut_dossier__code=dossier_code)

        if has_jurist == "avec":
            qs = qs.filter(has_jurist=True)
        elif has_jurist == "sans":
            qs = qs.filter(has_jurist=False)

        if has_conseille == "avec":
            qs = qs.filter(has_conseiller=True)
        elif has_conseille == "sans":
            qs = qs.filter(has_conseiller=False)

        # --- Total avant pagination ---
        total = qs.count()

        # --- Tri, pagination ---
        qs = qs.order_by(ordering)
        start = (page - 1) * page_size
        end = start + page_size

        rows = list(
            qs.values(
                "id",
                "first_name",
                "last_name",
                "email",
                "phone",
                "created_at",
                "appointment_date",
                # IDs utiles pour tes sélecteurs
                "status_id",
                "statut_dossier_id",
                # Lead status
                "lead_status_code",
                "lead_status_label",
                "lead_status_color",
                # Dossier status
                "statut_dossier_code",
                "statut_dossier_label",
                "statut_dossier_color",
                # Flags
                "has_conseiller",
                "has_jurist",
            )[start:end]
        )

        return Response(
            {
                "total": total,
                "page": page,
                "page_size": page_size,
                "ordering": ordering,
                "items": rows,
            }
        )
