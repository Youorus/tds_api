from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.utils import timezone
from api.utils.contract_generator import generate_contract_pdf


class Contract(models.Model):
    client = models.ForeignKey("api.Client", on_delete=models.CASCADE, related_name="contracts")
    created_by = models.ForeignKey("api.User", on_delete=models.SET_NULL, null=True, blank=True)
    service = models.ForeignKey("api.Service", on_delete=models.PROTECT, related_name="contracts")
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    contract_url = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    is_signed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    @property
    def real_amount(self):
        ratio = Decimal("1.00") - (self.discount_percent / Decimal("100.00"))
        return (self.amount_due * ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def amount_paid(self):
        return sum(receipt.amount for receipt in self.receipts.all())

    @property
    def is_fully_paid(self):
        return self.real_amount <= self.amount_paid

    def __str__(self):
        return f"Contrat {self.id} - {self.client.full_name}"

    def generate_pdf(self):
        from api.utils.store_cloud import store_contract_pdf
        """
        Génère un PDF pour le contrat et met à jour son URL.
        """
        if self.contract_url:
            print("ℹ️ PDF déjà généré, URL :", self.contract_url)
            return self.contract_url

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