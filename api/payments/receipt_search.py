from django.db import models
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status

from api.payments.models import PaymentReceipt
from api.payments.serializers import PaymentReceiptSerializer


def get_filtered_receipts(params):
    queryset = PaymentReceipt.objects.all()

    # Plein texte sur client, mode...
    search = params.get("search")
    if search:
        queryset = queryset.filter(
            Q(client__first_name__icontains=search) |
            Q(client__last_name__icontains=search) |
            Q(mode__icontains=search)
        )

    # Filtre par client
    client = params.get("client")
    if client:
        queryset = queryset.filter(client_id=client)

    # Filtre par contrat
    contract = params.get("contract")
    if contract:
        queryset = queryset.filter(contract_id=contract)

    # Filtre par créateur
    created_by = params.get("created_by")
    if created_by:
        queryset = queryset.filter(created_by_id=created_by)

    # --- Filtre par date d’échéance (next_due_date) ---
    period_type = params.get("period_type")
    date_field = "next_due_date"  # <-- on filtre sur ce champ ici !

    if period_type == "day":
        day = params.get("date")
        if day:
            queryset = queryset.filter(**{f"{date_field}": day})

    elif period_type == "range":
        from_date = params.get("from")
        to_date = params.get("to")
        if from_date and to_date:
            queryset = queryset.filter(**{
                f"{date_field}__gte": from_date,
                f"{date_field}__lte": to_date
            })

    elif period_type == "month":
        month = params.get("month")
        year = params.get("year")
        if month and year:
            queryset = queryset.filter(**{
                f"{date_field}__year": int(year),
                f"{date_field}__month": int(month)
            })

    elif period_type == "year":
        year = params.get("year")
        if year:
            queryset = queryset.filter(**{
                f"{date_field}__year": int(year)
            })

    # (optionnel) Ne renvoyer que les paiements à venir (date future)
    only_upcoming = params.get("upcoming")
    if str(only_upcoming).lower() in ("1", "true", "yes", "oui"):
        from django.utils import timezone
        today = timezone.now().date()
        queryset = queryset.filter(next_due_date__gte=today)

    return queryset.order_by("next_due_date")  # échéances à venir en premier

class PaymentReceiptSearchAPIView(APIView):
    """
    Recherche avancée des échéances de paiement à venir.
    """
    def get(self, request):
        params = request.query_params
        queryset = get_filtered_receipts(params)

        paginator = PageNumberPagination()
        paginator.page_size_query_param = "page_size"
        page = paginator.paginate_queryset(queryset, request)
        serializer = PaymentReceiptSerializer(page, many=True) if page is not None else PaymentReceiptSerializer(queryset, many=True)

        # Optionnel : somme totale à régler sur cette sélection
        total_due = queryset.aggregate(total=models.Sum("amount"))["total"] or 0

        response_data = {
            "results": serializer.data,
            "count": queryset.count(),
            "total_due": float(total_due),
        }

        if page is not None:
            paginated = paginator.get_paginated_response(serializer.data)
            paginated.data["total_due"] = float(total_due)
            return paginated
        else:
            return Response(response_data, status=status.HTTP_200_OK)