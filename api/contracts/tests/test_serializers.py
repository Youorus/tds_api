import pytest
from decimal import Decimal
from django.utils import timezone
from api.contracts.models import Contract
from api.clients.models import Client
from api.contracts.serializer import ContractSerializer
from api.services.models import Service
from api.users.models import User

"""
Vérifie que le serializer `ContractSerializer` retourne les valeurs calculées correctement :
- Montant dû réel après remise
- Montant payé, net payé et solde dû
- Statut de paiement
"""
@pytest.mark.django_db
def test_contract_serializer_values():
    from api.leads.models import Lead
    from api.lead_status.models import LeadStatus

    status, _ = LeadStatus.objects.get_or_create(code="NOUVEAU", defaults={"label": "Nouveau", "color": "#000000"})

    lead = Lead.objects.create(
        first_name="Marc",
        last_name="Dupont",
        phone="+33600000000",
        status=status
    )

    client = Client.objects.create(lead=lead)

    service = Service.objects.create(
        code="VISA_LONG",
        label="Visa long séjour",
        price=Decimal("1000.00")
    )

    user = User.objects.create_user(
        email="test@example.com",
        first_name="Admin",
        last_name="User",
        password="securepassword123",
        role="ADMIN"
    )

    contract = Contract.objects.create(
        client=client,
        service=service,
        created_by=user,
        amount_due=Decimal("1000.00"),
        discount_percent=Decimal("20.00"),
        refund_amount=Decimal("100.00"),
        contract_url="https://example.com/contract.pdf",
        is_signed=True,
        created_at=timezone.now()
    )

    contract.receipts.create(amount=Decimal("500.00"), client=client)

    serializer = ContractSerializer(contract)
    data = serializer.data

    assert data["amount_due"] == "1000.00"
    assert data["discount_percent"] == "20.00"
    assert data["real_amount_due"] == Decimal("800.00")       # 1000 * 0.8
    assert data["amount_paid"] == Decimal("500.00")
    assert data["net_paid"] == Decimal("400.00")                # 500 - 100
    assert data["balance_due"] == Decimal("400.00")             # 800 - 400
    assert data["is_fully_paid"] is False
    assert data["contract_url"] == "https://example.com/contract.pdf"
    assert data["client"] == contract.client.id
    assert data["service"] == contract.service.id
    assert data["is_signed"] is True