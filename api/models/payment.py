from decimal import Decimal, ROUND_HALF_UP
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ServiceTarifaire(models.TextChoices):
    TITRE_SEJOUR = "TITRE_SEJOUR", _("Titre de séjour")
    REGROUPEMENT_FAMILIAL = "REGROUPEMENT_FAMILIAL", _("Regroupement familial")
    NATURALISATION = "NATURALISATION", _("Naturalisation")
    RENOUVELLEMENT = "RENOUVELLEMENT", _("Renouvellement")
    SUIVI_NATURALISATION = "SUIVI_NATURALISATION", _("Suivi naturalisation")
    DEMANDE_VISA = "DEMANDE_VISA", _("Demande de visa")
    DUPLICATA = "DUPLICATA", _("Duplicata")
    SUIVI_DOSSIER = "SUIVI_DOSSIER", _("Suivi dossier")
    DCEM = "DCEM", _("DCEM")


class PaymentMode(models.TextChoices):
    ESPECES = "ESPECES", _("Espèces")
    CB = "CB", _("Carte bancaire")
    VIREMENT = "VIREMENT", _("Virement")
    CHEQUE = "CHEQUE", _("Chèque")
    PNF = "PNF", _("Crédit Cofidis (PNL)")


SERVICE_PRICES = {
    ServiceTarifaire.TITRE_SEJOUR: Decimal("1590.00"),
    ServiceTarifaire.REGROUPEMENT_FAMILIAL: Decimal("1590.00"),
    ServiceTarifaire.NATURALISATION: Decimal("1290.00"),
    ServiceTarifaire.RENOUVELLEMENT: Decimal("990.00"),
    ServiceTarifaire.SUIVI_NATURALISATION: Decimal("990.00"),
    ServiceTarifaire.DEMANDE_VISA: Decimal("990.00"),
    ServiceTarifaire.DUPLICATA: Decimal("990.00"),
    ServiceTarifaire.SUIVI_DOSSIER: Decimal("690.00"),
    ServiceTarifaire.DCEM: Decimal("590.00"),
}


class Payment(models.Model):
    client = models.ForeignKey("api.Client", on_delete=models.CASCADE, related_name="payment_plans")
    created_by = models.ForeignKey("api.User", on_delete=models.SET_NULL, null=True, blank=True)
    service = models.CharField(max_length=50, choices=ServiceTarifaire.choices)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    next_due_date = models.DateField(null=True, blank=True)
    contract_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    @property
    def real_amount_due(self):
        discount_ratio = Decimal("1.00") - (self.discount_percent / Decimal("100.00"))
        return (self.amount_due * discount_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def amount_paid(self):
        return sum(receipt.amount for receipt in self.receipts.all())

    @property
    def is_fully_paid(self) -> bool:
        return self.remaining_amount == Decimal("0.00")


    @property
    def remaining_amount(self):
        return max(Decimal("0.00"), self.real_amount_due - self.amount_paid)

    def pay(self, *, amount: Decimal, mode: str, user, next_due_date=None):
        from api.models import PaymentReceipt
        from api.utils.contract_generator import generate_contract_pdf_sync  # <-- Ton utilitaire de contrat

        if amount <= 0:
            raise ValueError("Le montant du paiement doit être supérieur à zéro.")

        with transaction.atomic():
            receipt = PaymentReceipt.objects.create(
                client=self.client,
                plan=self,
                amount=amount,
                mode=mode,
                created_by=user,
            )
            receipt.generate_pdf()

            # GÉNÉRATION DU CONTRAT si c’est le premier paiement
            # GÉNÉRATION DU CONTRAT si non existant
            if not self.contract_url:
                lead = getattr(self.client, "lead", None)
                if not lead:
                    print(f"❌ Aucun lead lié au client {self.client}")
                else:
                    contract_data = {
                        "first_name": lead.first_name,
                        "last_name": lead.last_name,
                        "phone": lead.phone,
                        "email": lead.email,
                        "service": self.get_service_display(),
                        "montant": float(self.real_amount_due),
                    }

                    try:
                        contract_url = generate_contract_pdf_sync(contract_data)
                        if contract_url:
                            self.contract_url = contract_url
                            print(f"📄 Contrat généré pour {lead.first_name} {lead.last_name}: {contract_url}")
                        else:
                            print("❌ URL du contrat vide.")
                    except Exception as e:
                        print(f"❌ Erreur lors de la génération du contrat : {e}")

            # Mise à jour de l’échéance suivante
            total_after_payment = (self.amount_paid + amount).quantize(Decimal("0.01"))
            if total_after_payment >= self.real_amount_due:
                self.next_due_date = None
            elif next_due_date:
                self.next_due_date = next_due_date

            self.save(update_fields=["contract_url", "next_due_date"])

            return receipt