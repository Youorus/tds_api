from django.contrib.auth.models import update_last_login
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from api.serializers.login_serializer import LoginSerializer

User = get_user_model()

class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        tokens = serializer.validated_data['tokens']

        update_last_login(User, user)

        response_data = {
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "role": user.role,  # Valeur brute (ex: "ADMIN")
                "role_display": user.get_role_display(),  # Nom humain (ex: "Administrateur")
                "avatar": user.avatar,
                "last_login": user.last_login,
                "date_joined": user.date_joined,
            },
            "tokens": tokens
        }

        return Response(response_data, status=status.HTTP_200_OK)
