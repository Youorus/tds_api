import pytest
from decimal import Decimal
from api.contracts.serializer import ContractSerializer


@pytest.mark.django_db
def test_contract_serializer_output(contract):
    serializer = ContractSerializer(instance=contract)
    data = serializer.data
    assert "client" in data
    assert "amount_due" in data
    assert "real_amount_due" in data
    assert "is_fully_paid" in data

@pytest.mark.django_db
def test_contract_serializer_creation(client, user_admin, service):
    payload = {
        "client": client.id,
        "service": service.id,
        "amount_due": "200.00",
        "discount_percent": "5.00",
    }
    serializer = ContractSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors
    contract = serializer.save(created_by=user_admin)
    assert contract.amount_due == Decimal("200.00")
    assert contract.discount_percent == Decimal("5.00")