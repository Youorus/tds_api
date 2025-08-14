# api/leads/views.py
from datetime import date, datetime, time
from typing import Optional

from django.db.models import Exists, OuterRef, F
from django.utils.dateparse import parse_datetime, parse_date
from django.utils.timezone import make_aware, is_naive, get_current_timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.leads.models import Lead


def _parse_iso_any(dt: Optional[str]) -> Optional[object]:
    """
    Essaie de parser une string ISO en datetime OU date.
    - 'YYYY-MM-DDTHH:MM(:SS)' -> datetime (naïf)
    - 'YYYY-MM-DD'            -> date
    - None/''                 -> None
    """
    if not dt:
        return None
    return parse_datetime(dt) or parse_date(dt)


def _to_aware(dt_or_d: Optional[object], end_of_day: bool = False) -> Optional[datetime]:
    """
    Convertit une valeur (date ou datetime) en datetime timezone-aware, dans le TZ courant du projet.
    - Si 'date': construit un datetime à 00:00:00 (ou fin de journée si end_of_day=True).
    - Si 'datetime' naïf: make_aware().
    - Si 'datetime' déjà aware: inchangé.
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
    """Normalise 'avec'/'sans' (et alias) ou None."""
    if not value:
        return None
    v = value.strip().lower()
    if v in {"avec", "oui", "with", "true", "1"}:
        return "avec"
    if v in {"sans", "non", "without", "false", "0"}:
        return "sans"
    return None


def _to_int_or_none(val: Optional[str]) -> Optional[int]:
    """Convertit une string en int si possible, sinon None."""
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


class LeadSearchView(APIView):
    permission_classes = [IsAuthenticated]  # ajuste selon ton contexte

    def get(self, request):
        # --- Query params (bruts) ---
        raw_date_from = request.query_params.get("date_from")
        raw_date_to   = request.query_params.get("date_to")
        raw_appt_from = request.query_params.get("appt_from")
        raw_appt_to   = request.query_params.get("appt_to")

        # Filtres statut (code/ID)
        status_code   = request.query_params.get("status_code")         # ex: "RDV_CONFIRME"
        status_id     = _to_int_or_none(request.query_params.get("status_id"))
        dossier_code  = request.query_params.get("dossier_code")        # ex: "A_TRAITER"
        dossier_id    = _to_int_or_none(request.query_params.get("dossier_id"))

        # Filtres binaires
        has_jurist    = _normalize_avec_sans(request.query_params.get("has_jurist"))         # 'avec'|'sans'|None
        has_conseille = _normalize_avec_sans(request.query_params.get("has_conseiller"))     # 'avec'|'sans'|None

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
            "created_at", "-created_at",
            "appointment_date", "-appointment_date",
            "id", "-id",
        }
        ordering = request.query_params.get("ordering", "-created_at")
        if ordering not in allowed_ordering:
            ordering = "-created_at"

        # --- Parse & normalize dates (timezone-aware) ---
        date_from_any = _parse_iso_any(raw_date_from)  # date ou datetime
        date_to_any   = _parse_iso_any(raw_date_to)
        appt_from_any = _parse_iso_any(raw_appt_from)
        appt_to_any   = _parse_iso_any(raw_appt_to)

        date_from = _to_aware(date_from_any, end_of_day=False)
        date_to   = _to_aware(date_to_any,   end_of_day=True)   # inclure toute la journée
        appt_from = _to_aware(appt_from_any, end_of_day=False)
        appt_to   = _to_aware(appt_to_any,   end_of_day=True)

        # --- Base queryset + annotations utiles ---
        ThroughConseiller = Lead.assigned_to.through
        ThroughJurist     = Lead.jurist_assigned.through

        qs = (
            Lead.objects
            .select_related("status", "statut_dossier")
            .annotate(
                has_conseiller=Exists(ThroughConseiller.objects.filter(lead_id=OuterRef("pk"))),
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
        )

        # --- Filtres de période (création) ---
        if date_from:
            qs = qs.filter(created_at__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)

        # --- Filtres de période (appointment) ---
        if appt_from:
            qs = qs.filter(appointment_date__isnull=False, appointment_date__gte=appt_from)
        if appt_to:
            qs = qs.filter(appointment_date__isnull=False, appointment_date__lte=appt_to)

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

        rows = list(qs.values(
            "id", "first_name", "last_name", "email", "phone",
            "created_at", "appointment_date",
            # IDs utiles pour tes sélecteurs
            "status_id", "statut_dossier_id",
            # Lead status
            "lead_status_code", "lead_status_label", "lead_status_color",
            # Dossier status
            "statut_dossier_code", "statut_dossier_label", "statut_dossier_color",
            # Flags
            "has_conseiller", "has_jurist",
        )[start:end])

        return Response({
            "total": total,
            "page": page,
            "page_size": page_size,
            "ordering": ordering,
            "items": rows,
        })