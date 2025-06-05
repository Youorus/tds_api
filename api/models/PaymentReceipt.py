from django.db import models
from django.utils import timezone
from api.models.payment import Payment, PaymentMode
from api.utils.receipt_generator import generate_receipt_pdf_sync


class PaymentReceipt(models.Model):
    client = models.ForeignKey("api.Client", on_delete=models.CASCADE, related_name="receipts")
    plan = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="receipts")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mode = models.CharField(max_length=20, choices=PaymentMode.choices)
    payment_date = models.DateTimeField(default=timezone.now)
    receipt_url = models.URLField(blank=True, null=True)
    created_by = models.ForeignKey("api.User", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-payment_date"]

    def __str__(self):
        return f"{self.client} - {self.amount} € - {self.payment_date.date()}"

    def generate_pdf(self):
        self.receipt_url = generate_receipt_pdf_sync(self)
        self.save(update_fields=["receipt_url"])
