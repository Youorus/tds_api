import pytest
from decimal import Decimal
from api.contracts.models import Contract
from api.clients.models import Client
from api.contracts.serializer import ContractSerializer
from api.services.models import Service
from api.users.models import User
from api.lead_status.models import LeadStatus

@pytest.mark.django_db
class TestContractSerializer:
    @pytest.fixture
    def contract(self):
        # 1. Création du LeadStatus requis par Lead
        status = LeadStatus.objects.create(code="NOUVEAU", label="Nouveau")
        # 2. Création d’un user
        user = User.objects.create_user(
            email="test@user.com", first_name="Marc", last_name="Nkue", password="pwd", role="ADMIN"
        )
        # 3. Création d’un lead avec status
        from api.leads.models import Lead
        lead = Lead.objects.create(first_name="Marc", last_name="Nkue", status=status)
        # 4. Création d’un client lié au lead
        client = Client.objects.create(lead=lead)
        # 5. Création du service (selon tes champs)
        service = Service.objects.create(code="TDS", label="Titre de séjour", price=Decimal("120.00"))
        # 6. Création du contrat
        contract = Contract.objects.create(
            client=client,
            created_by=user,
            service=service,
            amount_due=Decimal("200.00"),
            discount_percent=Decimal("10.00")
        )
        return contract

    def test_serializer_outputs_all_fields(self, contract):
        serializer = ContractSerializer(contract)
        data = serializer.data
        assert "id" in data
        assert "client" in data
        assert "service" in data
        assert "amount_due" in data
        assert "discount_percent" in data
        assert "real_amount_due" in data
        assert "amount_paid" in data
        assert "is_fully_paid" in data
        assert Decimal(data["real_amount_due"]) == Decimal("180.00")
        assert data["amount_paid"] == 0
        assert data["is_fully_paid"] is False

    def test_is_fully_paid_true(self, contract, monkeypatch):
        monkeypatch.setattr(type(contract), "amount_paid", property(lambda self: Decimal("180.00")))
        assert contract.is_fully_paid

    def test_validation_error_on_missing_fields(self):
        data = {
            "amount_due": "100.00",
            "discount_percent": "5.00"
        }
        serializer = ContractSerializer(data=data)
        assert not serializer.is_valid()
        assert "client" in serializer.errors or "service" in serializer.errors