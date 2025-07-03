# models.py
from django.db import models
from decimal import Decimal

class Service(models.Model):
    code = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)             # ex: "Titre de séjour"
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    def __str__(self):
        return f"{self.label} ({self.price} €)"