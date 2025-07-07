import pytest
from decimal import Decimal
from django.utils import timezone
from api.models import PaymentReceipt, Client, Contract, User

@pytest.mark.django_db
def test_receipt_creation_and_str(client_factory, contract_factory, user_factory):
    client = client_factory()
    contract = contract_factory(client=client)
    user = user_factory(role="ADMIN")
    receipt = PaymentReceipt.objects.create(
        client=client,
        contract=contract,
        amount=Decimal("100.00"),
        mode="CB",
        created_by=user,
        payment_date=timezone.now()
    )
    assert str(receipt).startswith(f"Reçu 100.00 €")
    assert receipt.client == client
    assert receipt.contract == contract
    assert receipt.amount == Decimal("100.00")
    assert receipt.mode == "CB"
    assert receipt.created_by == user

@pytest.mark.django_db
def test_next_due_date_optional(client_factory, contract_factory):
    client = client_factory()
    contract = contract_factory(client=client)
    receipt = PaymentReceipt.objects.create(
        client=client,
        contract=contract,
        amount=Decimal("50.00"),
        mode="ESPECES",
    )
    assert receipt.next_due_date is None