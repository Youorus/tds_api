from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class Contract(models.Model):
    """
    Modèle représentant un contrat client, lié à un service, un utilisateur créateur et un client.
    - Gère le montant, remise, PDF, paiements et signature.
    """
    client = models.ForeignKey("clients.Client", on_delete=models.CASCADE, related_name="contracts")
    created_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True)
    service = models.ForeignKey("services.Service", on_delete=models.PROTECT, related_name="contracts")
    amount_due = models.DecimalField(_("Montant dû (€)"), max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(_("Remise (%)"), max_digits=5, decimal_places=2, default=Decimal("0.00"))
    contract_url = models.URLField(_("Contrat PDF"), blank=True, null=True)
    created_at = models.DateTimeField(_("Créé le"), default=timezone.now)
    is_signed = models.BooleanField(_("Signé ?"), default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("contrat")
        verbose_name_plural = _("contrats")

    @property
    def real_amount(self):
        """Montant réel dû après remise."""
        ratio = Decimal("1.00") - (self.discount_percent / Decimal("100.00"))
        return (self.amount_due * ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def amount_paid(self):
        """Somme totale déjà payée via les reçus liés."""
        return sum(receipt.amount for receipt in self.receipts.all())

    @property
    def is_fully_paid(self):
        """Contrat soldé si montant réel dû <= total payé."""
        return self.real_amount <= self.amount_paid

    def __str__(self):
        return f"Contrat {self.id} - {getattr(self.client, 'full_name', self.client.pk)}"

    def generate_pdf(self):
        """
        Génère un PDF pour le contrat (stockage cloud).
        Renvoie l’URL du contrat PDF.
        """
        if self.contract_url:
            print("ℹ️ PDF déjà généré, URL :", self.contract_url)
            return self.contract_url

        from api.utils.pdf.contract_generator import generate_contract_pdf
        from api.utils.cloud.storage import store_contract_pdf
        print(f"📄 Génération PDF pour contrat #{self.pk}...")
        try:
            pdf_bytes = generate_contract_pdf(self)
            contract_url = store_contract_pdf(self, pdf_bytes)
            if contract_url:
                self.contract_url = contract_url
                Contract.objects.filter(pk=self.pk).update(contract_url=contract_url)
                print("✅ Contrat PDF généré :", contract_url)
            else:
                print("⚠️ Aucune URL retournée par store_contract_pdf")
            return contract_url
        except Exception as e:
            print(f"❌ Erreur lors de la génération du contrat PDF : {e}")
            return None