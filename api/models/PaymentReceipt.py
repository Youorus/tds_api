from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from api.utils.receipt_generator import generate_receipt_pdf
from api.utils.store_cloud import store_receipt_pdf


class PaymentMode(models.TextChoices):
    ESPECES = "ESPECES", _("Espèces")
    CB = "CB", _("Carte bancaire")
    VIREMENT = "VIREMENT", _("Virement")
    CHEQUE = "CHEQUE", _("Chèque")
    PNF = "PNF", _("Crédit Cofidis (PNF)")

class PaymentReceipt(models.Model):
    client = models.ForeignKey(
        "api.Client",
        on_delete=models.CASCADE,
        related_name="receipts"
    )
    contract = models.ForeignKey(
        "api.Contract",
        on_delete=models.CASCADE,
        related_name="receipts",
        null=True
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    mode = models.CharField(
        max_length=20,
        choices=PaymentMode.choices
    )
    payment_date = models.DateTimeField(
        default=timezone.now
    )
    next_due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date de la prochaine échéance prévue si le contrat n'est pas encore soldé."
    )
    receipt_url = models.URLField(
        blank=True,
        null=True
    )
    created_by = models.ForeignKey(
        "api.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-payment_date"]

    def __str__(self):
        return f"Reçu {self.amount:.2f} € - {self.client} - {self.payment_date.date()}"

    def generate_pdf(self):
        """
        Génère un reçu PDF et met à jour l'URL.
        """
        pdf_bytes = generate_receipt_pdf(self)
        url = store_receipt_pdf(self, pdf_bytes)
        if url:
            PaymentReceipt.objects.filter(pk=self.pk).update(receipt_url=url)