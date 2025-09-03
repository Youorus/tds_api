# api/contracts/test_views.py
from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from django.db.models import (
    BooleanField,
    Case,
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    Max,
    Min,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce, Greatest
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import get_current_timezone, is_naive, make_aware
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.contracts.models import Contract


def _parse_iso_any(dt: Optional[str]) -> Optional[object]:
    if not dt:
        return None
    return parse_datetime(dt) or parse_date(dt)


def _to_aware(
    dt_or_d: Optional[object], end_of_day: bool = False
) -> Optional[datetime]:
    if dt_or_d is None:
        return None
    tz = get_current_timezone()
    if isinstance(dt_or_d, date) and not isinstance(dt_or_d, datetime):
        dtime = datetime.combine(
            dt_or_d, time(23, 59, 59, 999999) if end_of_day else time(0, 0, 0, 0)
        )
        return make_aware(dtime, timezone=tz)
    if is_naive(dt_or_d):
        return make_aware(dt_or_d, timezone=tz)
    return dt_or_d


def _normalize_avec_sans(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    v = value.strip().lower()
    if v in {"avec", "oui", "with", "true", "1"}:
        return "avec"
    if v in {"sans", "non", "without", "false", "0"}:
        return "sans"
    return None


def _to_dec(v: Optional[str]) -> Optional[Decimal]:
    if v is None or v == "":
        return None
    try:
        return Decimal(str(v))
    except Exception:
        return None


def _to_int_or_str(v: Optional[str]) -> Optional[str]:
    if v is None or str(v).strip() == "":
        return None
    return str(v).strip()


def _dec(v: Optional[Decimal]) -> float:
    return float(v or Decimal("0.00"))


class ContractSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        raw_date_from = request.query_params.get("date_from")
        raw_date_to = request.query_params.get("date_to")

        is_signed_param = _normalize_avec_sans(request.query_params.get("is_signed"))
        is_refunded_param = _normalize_avec_sans(
            request.query_params.get("is_refunded")
        )
        fully_paid_param = _normalize_avec_sans(
            request.query_params.get("is_fully_paid")
        )
        has_balance_param = _normalize_avec_sans(
            request.query_params.get("has_balance")
        )
        with_discount = _normalize_avec_sans(request.query_params.get("with_discount"))

        service_id = _to_int_or_str(request.query_params.get("service_id"))
        service_code = request.query_params.get("service_code")
        client_id = _to_int_or_str(request.query_params.get("client_id"))
        created_by = _to_int_or_str(request.query_params.get("created_by"))

        min_amount_due = _to_dec(request.query_params.get("min_amount_due"))
        max_amount_due = _to_dec(request.query_params.get("max_amount_due"))
        min_real_amount = _to_dec(request.query_params.get("min_real_amount"))
        max_real_amount = _to_dec(request.query_params.get("max_real_amount"))
        min_balance_due = _to_dec(request.query_params.get("min_balance_due"))
        max_balance_due = _to_dec(request.query_params.get("max_balance_due"))

        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except Exception:
            page = 1
        try:
            page_size = min(max(int(request.query_params.get("page_size", 20)), 1), 200)
        except Exception:
            page_size = 20

        allowed_ordering = {
            "created_at",
            "-created_at",
            "amount_due",
            "-amount_due",
            "real_amount_due",
            "-real_amount_due",
            "amount_paid",
            "-amount_paid",
            "net_paid",
            "-net_paid",
            "balance_due",
            "-balance_due",
            "id",
            "-id",
        }
        ordering = request.query_params.get("ordering", "-created_at")
        if ordering not in allowed_ordering:
            ordering = "-created_at"

        date_from = _to_aware(_parse_iso_any(raw_date_from), end_of_day=False)
        date_to = _to_aware(_parse_iso_any(raw_date_to), end_of_day=True)

        real_amount_due = ExpressionWrapper(
            F("amount_due")
            * (
                Value(1.0)
                - (
                    Coalesce(F("discount_percent"), Value(Decimal("0.00")))
                    / Value(100.0)
                )
            ),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        amount_paid = Coalesce(Sum("receipts__amount"), Value(Decimal("0.00")))
        net_paid = Greatest(
            Value(Decimal("0.00")),
            ExpressionWrapper(
                amount_paid - Coalesce(F("refund_amount"), Value(Decimal("0.00"))),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )
        balance_due = Greatest(
            Value(Decimal("0.00")),
            ExpressionWrapper(
                real_amount_due - net_paid,
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )
        today = timezone.localdate()

        qs = (
            Contract.objects.select_related("client", "service", "created_by")
            .annotate(
                real_amount_due=real_amount_due,
                amount_paid=amount_paid,
                net_paid=net_paid,
                balance_due=balance_due,
                # ⇩⇩⇩ ANNOTATION CLÉ pour les remises (évite toute comparaison d'expressions)
                discount_abs=Coalesce(F("discount_percent"), Value(Decimal("0.00"))),
            )
            .annotate(
                is_fully_paid=Case(
                    When(balance_due=Decimal("0.00"), then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
                next_due_date=Min(
                    "receipts__next_due_date",
                    filter=Q(receipts__next_due_date__gte=today),
                ),
                last_payment_date=Max("receipts__payment_date"),
            )
        )

        if date_from:
            qs = qs.filter(created_at__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)

        if is_signed_param == "avec":
            qs = qs.filter(is_signed=True)
        elif is_signed_param == "sans":
            qs = qs.filter(is_signed=False)

        if is_refunded_param == "avec":
            qs = qs.filter(is_refunded=True)
        elif is_refunded_param == "sans":
            qs = qs.filter(is_refunded=False)

        if fully_paid_param == "avec":
            qs = qs.filter(balance_due=Decimal("0.00"))
        elif fully_paid_param == "sans":
            qs = qs.filter(balance_due__gt=Decimal("0.00"))

        if has_balance_param == "avec":
            qs = qs.filter(balance_due__gt=Decimal("0.00"))
        elif has_balance_param == "sans":
            qs = qs.filter(balance_due=Decimal("0.00"))

        # ✅ Remplace toute comparaison « expression > Decimal » par un lookup sur l’annotation
        if with_discount == "avec":
            qs = qs.filter(discount_abs__gt=Decimal("0.00"))
        elif with_discount == "sans":
            qs = qs.filter(discount_abs__lte=Decimal("0.00"))

        if service_id:
            qs = qs.filter(service_id=service_id)
        if service_code:
            qs = qs.filter(service__code=service_code)
        if client_id:
            qs = qs.filter(client_id=client_id)
        if created_by:
            qs = qs.filter(created_by_id=created_by)

        if min_amount_due is not None:
            qs = qs.filter(amount_due__gte=min_amount_due)
        if max_amount_due is not None:
            qs = qs.filter(amount_due__lte=max_amount_due)
        if min_real_amount is not None:
            qs = qs.filter(real_amount_due__gte=min_real_amount)
        if max_real_amount is not None:
            qs = qs.filter(real_amount_due__lte=max_real_amount)
        if min_balance_due is not None:
            qs = qs.filter(balance_due__gte=min_balance_due)
        if max_balance_due is not None:
            qs = qs.filter(balance_due__lte=max_balance_due)

        # Agrégats (aucune comparaison Python entre expressions ici)
        agg = qs.aggregate(
            sum_amount_due=Coalesce(Sum("amount_due"), Value(Decimal("0.00"))),
            sum_real_amount_due=Coalesce(
                Sum("real_amount_due"), Value(Decimal("0.00"))
            ),
            sum_amount_paid=Coalesce(Sum("amount_paid"), Value(Decimal("0.00"))),
            sum_net_paid=Coalesce(Sum("net_paid"), Value(Decimal("0.00"))),
            sum_balance_due=Coalesce(Sum("balance_due"), Value(Decimal("0.00"))),
            count_signed=Count("id", filter=Q(is_signed=True)),
            count_refunded=Count("id", filter=Q(is_refunded=True)),
            count_fully_paid=Count("id", filter=Q(balance_due=Decimal("0.00"))),
            count_with_balance=Count("id", filter=Q(balance_due__gt=Decimal("0.00"))),
            # ✅ utilisation de l’annotation discount_abs
            count_reduced=Count("id", filter=Q(discount_abs__gt=Decimal("0.00"))),
        )

        total = qs.count()

        qs = qs.order_by(ordering)
        start = (page - 1) * page_size
        end = start + page_size

        rows = list(
            qs.values(
                "id",
                "client_id",
                "service_id",
                "created_by_id",
                "client__lead__first_name",
                "client__lead__last_name",
                "client__lead__email",
                "client__lead__phone",
                "service__code",
                "service__label",
                "service__price",
                "created_by__first_name",
                "created_by__last_name",
                "amount_due",
                "discount_percent",
                "real_amount_due",
                "amount_paid",
                "net_paid",
                "balance_due",
                "is_fully_paid",
                "is_refunded",
                "refund_amount",
                "is_signed",
                "contract_url",
                "created_at",
                "next_due_date",
                "last_payment_date",
            )[start:end]
        )

        return Response(
            {
                "total": total,
                "page": page,
                "page_size": page_size,
                "ordering": ordering,
                "aggregates": {
                    "sum_amount_due": _dec(agg["sum_amount_due"]),
                    "sum_real_amount_due": _dec(agg["sum_real_amount_due"]),
                    "sum_amount_paid": _dec(agg["sum_amount_paid"]),
                    "sum_net_paid": _dec(agg["sum_net_paid"]),
                    "sum_balance_due": _dec(agg["sum_balance_due"]),
                    "count_signed": int(agg["count_signed"] or 0),
                    "count_refunded": int(agg["count_refunded"] or 0),
                    "count_fully_paid": int(agg["count_fully_paid"] or 0),
                    "count_with_balance": int(agg["count_with_balance"] or 0),
                    "count_reduced": int(agg["count_reduced"] or 0),
                },
                "items": rows,
            }
        )
