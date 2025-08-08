# api/leads/lead_search.py

from django.db.models import Q
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from api.leads.models import Lead
from api.leads.serializers import LeadSerializer

def get_filtered_leads(params):
    queryset = Lead.objects.all()

    # 1. Plein texte
    search = params.get("search")
    if search:
        queryset = queryset.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )

    # 2. Filtre par statut(s)
    status = params.get("status")
    if status:
        queryset = queryset.filter(status_id=status)
    status_code = params.get("status_code")
    if status_code:
        queryset = queryset.filter(status__code=status_code.upper())
    status_in = params.get("status_in")
    if status_in:
        ids = [int(s) for s in status_in.split(",") if s.isdigit()]
        queryset = queryset.filter(status_id__in=ids)
    status_code_in = params.get("status_code_in")
    if status_code_in:
        codes = [s.upper() for s in status_code_in.split(",") if s.strip()]
        queryset = queryset.filter(status__code__in=codes)

    # 3. Filtre par statut de dossier
    statut_dossier = params.get("statut_dossier")
    if statut_dossier:
        queryset = queryset.filter(statut_dossier_id=statut_dossier)
    statut_dossier_code = params.get("statut_dossier_code")
    if statut_dossier_code:
        queryset = queryset.filter(statut_dossier__code=statut_dossier_code.upper())
    statut_dossier_in = params.get("statut_dossier_in")
    if statut_dossier_in:
        ids = [int(s) for s in statut_dossier_in.split(",") if s.isdigit()]
        queryset = queryset.filter(statut_dossier_id__in=ids)
    statut_dossier_code_in = params.get("statut_dossier_code_in")
    if statut_dossier_code_in:
        codes = [s.upper() for s in statut_dossier_code_in.split(",") if s.strip()]
        queryset = queryset.filter(statut_dossier__code__in=codes)

    # 4. Filtre par date/période
    period_type = params.get("period_type")  # "day", "range", "month", "year", "all"
    date_field = params.get("date_field", "created_at")
    if date_field not in ["created_at", "appointment_date"]:
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

    # 5. Autres filtres personnalisés (assigned_to, jurist_assigned…)
    assigned_to = params.get("assigned_to")
    if assigned_to:
        queryset = queryset.filter(assigned_to__id=assigned_to)
    jurist_assigned = params.get("jurist_assigned")
    if jurist_assigned:
        queryset = queryset.filter(jurist_assigned__id=jurist_assigned)
    # ... Ajoute d'autres filtres si besoin ...

    return queryset.order_by("-created_at")


class LeadSearchAPIView(APIView):
    """
    Recherche avancée de leads (statut, statut dossier, période, etc) avec pagination DRF.
    """

    def get(self, request):
        params = request.query_params
        queryset = get_filtered_leads(params)

        paginator = PageNumberPagination()
        paginator.page_size_query_param = "page_size"
        page = paginator.paginate_queryset(queryset, request)
        serializer = LeadSerializer(page, many=True) if page is not None else LeadSerializer(queryset, many=True)

        if page is not None:
            return paginator.get_paginated_response(serializer.data)
        else:
            return Response({
                "results": serializer.data,
                "count": queryset.count()
            }, status=status.HTTP_200_OK)
