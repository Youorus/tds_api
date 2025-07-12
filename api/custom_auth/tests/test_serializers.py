import pytest
from django.contrib.auth import get_user_model
from api.custom_auth.serializers import LoginSerializer

User = get_user_model()

@pytest.mark.django_db
class TestLoginSerializer:
    @pytest.fixture
    def user(self):
        user = User.objects.create_user(
            email="test@ex.com", first_name="Marc", last_name="Nkue", password="azerty123", role="ADMIN"
        )
        user.is_active = True
        user.save()
        return user

    def test_valid_credentials(self, user):
        data = {"email": user.email, "password": "azerty123"}
        serializer = LoginSerializer(data=data, context={"request": None})
        assert serializer.is_valid()
        assert serializer.validated_data["user"] == user

    def test_invalid_email(self):
        data = {"email": "nobody@ex.com", "password": "whatever"}
        serializer = LoginSerializer(data=data, context={"request": None})
        with pytest.raises(Exception):
            serializer.is_valid(raise_exception=True)

    def test_wrong_password(self, user):
        data = {"email": user.email, "password": "WRONG"}
        serializer = LoginSerializer(data=data, context={"request": None})
        with pytest.raises(Exception):
            serializer.is_valid(raise_exception=True)

    def test_inactive_user(self, user):
        user.is_active = False
        user.save()
        data = {"email": user.email, "password": "azerty123"}
        serializer = LoginSerializer(data=data, context={"request": None})
        with pytest.raises(Exception):
            serializer.is_valid(raise_exception=True)