# api/contracts/contract_search.py

from django.db.models import Q, Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status

from api.contracts.models import Contract
from api.contracts.serializer import ContractSerializer


def get_filtered_contracts(params):
    queryset = Contract.objects.all()

    # Recherche plein texte (client, service, créateur, etc)
    search = params.get("search")
    if search:
        queryset = queryset.filter(
            Q(client__first_name__icontains=search) |
            Q(client__last_name__icontains=search) |
            Q(service__label__icontains=search) |
            Q(created_by__first_name__icontains=search) |
            Q(created_by__last_name__icontains=search)
        )

    # Filtre par service
    service = params.get("service")
    if service and service != "ALL":
        queryset = queryset.filter(service_id=service)

    service_in = params.get("service_in")
    if service_in:
        ids = [int(s) for s in service_in.split(",") if s.isdigit()]
        queryset = queryset.filter(service_id__in=ids)

    # Filtre par client
    client = params.get("client")
    if client and client != "ALL":
        queryset = queryset.filter(client_id=client)

    # Filtre par créateur
    created_by = params.get("created_by")
    if created_by and created_by != "ALL":
        queryset = queryset.filter(created_by_id=created_by)
    created_by_in = params.get("created_by_in")
    if created_by_in:
        ids = [int(s) for s in created_by_in.split(",") if s.isdigit()]
        queryset = queryset.filter(created_by_id__in=ids)

    # Filtre par signature
    is_signed = params.get("is_signed")
    if is_signed is not None:
        if str(is_signed).lower() in ("1", "true", "oui", "yes"):
            queryset = queryset.filter(is_signed=True)
        elif str(is_signed).lower() in ("0", "false", "non", "no"):
            queryset = queryset.filter(is_signed=False)

    # Filtre par date de création
    period_type = params.get("period_type")
    date_field = params.get("date_field", "created_at")
    if date_field not in ["created_at"]:
        date_field = "created_at"

    if period_type == "day":
        day = params.get("date")
        if day:
            queryset = queryset.filter(**{f"{date_field}__date": day})

    elif period_type == "range":
        from_date = params.get("from")
        to_date = params.get("to")
        if from_date and to_date:
            queryset = queryset.filter(**{
                f"{date_field}__date__gte": from_date,
                f"{date_field}__date__lte": to_date
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

    return queryset.order_by("-created_at")


class ContractSearchAPIView(APIView):
    """
    Recherche avancée de contrats avec stats (somme, etc).
    """
    def get(self, request):
        params = request.query_params
        queryset = get_filtered_contracts(params)

        paginator = PageNumberPagination()
        paginator.page_size_query_param = "page_size"
        page = paginator.paginate_queryset(queryset, request)
        serializer = ContractSerializer(page, many=True) if page is not None else ContractSerializer(queryset, many=True)

        # Calcul du montant total dû (et éventuellement autres agrégats)
        total_amount_due = queryset.aggregate(total=Sum("amount_due"))["total"] or 0

        response_data = {
            "results": serializer.data,
            "count": queryset.count(),
            "total_amount_due": float(total_amount_due),  # Pour JS/TS côté front
        }

        if page is not None:
            # Ajoute total à la pagination DRF (custom)
            paginated_response = paginator.get_paginated_response(serializer.data)
            paginated_response.data["total_amount_due"] = float(total_amount_due)
            return paginated_response
        else:
            return Response(response_data, status=status.HTTP_200_OK)