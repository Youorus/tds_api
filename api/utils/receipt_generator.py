import pdfkit
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django.utils import timezone

from api.storage_backends import MinioReceiptStorage
from api.models import PaymentReceipt

def generate_receipt_pdf_sync(receipt: PaymentReceipt) -> str:
    lead = receipt.client.lead

    context = {
        "receipt": receipt,
        "client_name": f"{lead.first_name} {lead.last_name}",
        "client_address": receipt.client.adresse or "Adresse non renseignée",
        "client_phone": lead.phone or "—",
        "client_email": lead.email or "—",
        "service": getattr(receipt.plan, "get_service_display", lambda: receipt.plan.service)(),
        "amount": f"{receipt.amount:.2f} €",
        "mode": getattr(receipt, "get_mode_display", lambda: receipt.mode)(),
        "remaining": f"{receipt.plan.remaining_amount:.2f} €",
        "date": timezone.now().strftime("%d/%m/%Y"),
        "company": {
            "name": "TDS France",
            "email": "contact@tds-france.fr",
            "website": "www.tds-france.fr",
            "siret": "928 184 043",
            "phones": ["01 85 09 01", "06 95 59 70 43"],
            "logo_url": "https://i.imgur.com/iSzPCvI.jpeg",
        },
    }

    html_string = render_to_string("recu/receipt_template.html", context)

    config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')  # adapte ce chemin si nécessaire

    pdf_file = pdfkit.from_string(html_string, False, configuration=config)

    filename = f"{receipt.id}_{slugify(f'{lead.last_name}_{lead.first_name}')}.pdf"
    file_content = ContentFile(pdf_file)
    storage = MinioReceiptStorage()
    saved_path = storage.save(filename, file_content)

    return storage.url(saved_path)