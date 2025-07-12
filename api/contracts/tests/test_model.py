import pytest
from decimal import Decimal
from api.contracts.models import Contract
from api.clients.models import Client
from api.users.models import User
from api.services.models import Service
from api.leads.models import Lead
from api.lead_status.models import LeadStatus
from unittest.mock import patch, PropertyMock

@pytest.mark.django_db
class TestContractModel:
    @pytest.fixture
    def contract(self):
        user = User.objects.create_user(
            email="test@user.com", first_name="Marc", last_name="Nkue", password="pwd", role="ADMIN"
        )
        status = LeadStatus.objects.create(code="NOUVEAU", label="Nouveau")
        lead = Lead.objects.create(first_name="Marc", last_name="Nkue", status=status)
        client = Client.objects.create(lead=lead)
        service = Service.objects.create(
            code="SERVICE_TEST",
            label="Service test",
            price=100
        )
        return Contract.objects.create(
            client=client,
            created_by=user,
            service=service,
            amount_due=Decimal("200.00"),
            discount_percent=Decimal("10.00")
        )

    def test_real_amount_calculation(self, contract):
        assert contract.real_amount == Decimal("180.00")

    def test_str_representation(self, contract):
        assert str(contract).startswith("Contrat")

    def test_is_fully_paid_property(self, contract):
        # Pas de reçus → pas payé
        assert not contract.is_fully_paid
        # Patch proprement la propriété amount_paid
        with patch.object(type(contract), "amount_paid", new_callable=PropertyMock) as mock_paid:
            mock_paid.return_value = Decimal("180.00")
            assert contract.is_fully_paid

    def test_generate_pdf_returns_url(self, contract, mocker):
        mocker.patch("api.utils.pdf.contract_generator.generate_contract_pdf", return_value=b"pdf")
        mocker.patch("api.utils.cloud.storage.store_contract_pdf", return_value="http://test/url.pdf")
        url = contract.generate_pdf()
        assert url == "http://test/url.pdf"