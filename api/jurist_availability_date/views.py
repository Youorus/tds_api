# api/views/jurist_availability_date.py

from rest_framework import viewsets, permissions

from api.jurist_availability_date.models import JuristGlobalAvailability
from api.jurist_availability_date.serializers import JuristGlobalAvailabilitySerializer
from rest_framework.decorators import action
from rest_framework.response import Response


class JuristGlobalAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = JuristGlobalAvailability.objects.all()
    serializer_class = JuristGlobalAvailabilitySerializer

    def get_permissions(self):
        # Lecture pour tous, écriture pour admin/staff
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    @action(detail=False, methods=["get"], url_path="days")
    def days(self, request):
        """
        Retourne la liste des jours (entiers 0-6) où il existe au moins un créneau global
        Ex : [1, 3] pour mardi/jeudi
        """
        days = (
            self.get_queryset()
            .values_list("day_of_week", flat=True)
            .distinct()
        )
        return Response(sorted(list(days)))