# api/views/me_view.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from api.serializers import UserSerializer


class MeView(APIView):
    """
    Endpoint : GET /me/
    Retourne les informations de l'utilisateur actuellement authentifié.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)