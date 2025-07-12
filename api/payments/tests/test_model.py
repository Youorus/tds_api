import pytest
from decimal import Decimal
from api.payments.models import PaymentReceipt
from api.clients.models import Client
from api.contracts.models import Contract
from api.services.models import Service
from api.users.models import User, UserRoles
from api.lead_status.models import LeadStatus
from api.leads.models import Lead

@pytest.mark.django_db
class TestPaymentReceiptModel:
    @pytest.fixture
    def payment_receipt(self):
        user = User.objects.create_user(
            email="pay@test.com", first_name="Pay", last_name="Ment", password="pwd", role=UserRoles.ADMIN
        )
        lead_status = LeadStatus.objects.create(code="NOUVEAU", label="Nouveau")
        lead = Lead.objects.create(first_name="Pay", last_name="Ment", status=lead_status)
        client = Client.objects.create(lead=lead)
        service = Service.objects.create(code="SERVICE_TEST", label="Service test", price=100)
        contract = Contract.objects.create(
            client=client,
            created_by=user,
            service=service,
            amount_due=Decimal("200.00"),
            discount_percent=Decimal("10.00"),
        )
        return PaymentReceipt.objects.create(
            client=client,
            contract=contract,
            amount=Decimal("100.00"),
            mode="CB",
            created_by=user,
        )

    def test_str(self, payment_receipt):
        assert "Reçu" in str(payment_receipt)

    def test_generate_pdf(self, payment_receipt, monkeypatch):
        monkeypatch.setattr("api.payments.models.generate_receipt_pdf", lambda self: b"pdf")
        monkeypatch.setattr("api.payments.models.store_receipt_pdf", lambda self, pdf: "http://dummy.pdf")
        payment_receipt.generate_pdf()
        # Test: après le call, le champ receipt_url a bien été update (si mock DB write ok)