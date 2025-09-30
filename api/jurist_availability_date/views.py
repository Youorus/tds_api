# api/views/jurist_availability_date.py

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import date

from api.jurist_availability_date.models import JuristGlobalAvailability
from api.jurist_availability_date.serializers import JuristGlobalAvailabilitySerializer


class JuristGlobalAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = JuristGlobalAvailability.objects.all()
    serializer_class = JuristGlobalAvailabilitySerializer

    def get_permissions(self):
        # Lecture pour tous, écriture pour admin/staff
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def days(self, request):
        """
        Retourne la liste des jours disponibles pour les juristes.
        - Si repeat_weekly=True → renvoie "weekly-<weekday>" (0=lundi, 6=dimanche)
        - Sinon → renvoie la date exacte "YYYY-MM-DD"
        """
        qs = self.get_queryset()
        days = set()
        for avail in qs:
            if avail.repeat_weekly:
                days.add(f"weekly-{avail.date.weekday()}")
            else:
                days.add(avail.date.isoformat())
        return Response(sorted(days))
