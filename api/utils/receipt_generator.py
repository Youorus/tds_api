import pdfkit
from django.template.loader import render_to_string
from django.utils import timezone
from api.models import PaymentReceipt


def generate_receipt_pdf(receipt: PaymentReceipt) -> bytes:
    lead = receipt.client.lead
    contract = receipt.contract

    context = {
        "receipt": receipt,
        "client_name": f"{lead.first_name} {lead.last_name}",
        "client_address": receipt.client.adresse or "Adresse non renseignée",
        "client_phone": lead.phone or "—",
        "client_email": lead.email or "—",
        "service": contract.service,
        "amount": f"{receipt.amount:.2f} €",
        "mode": receipt.get_mode_display(),
        "remaining": f"{(contract.real_amount - contract.amount_paid):.2f} €",
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
    config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')  # adapte ce chemin si besoin
    pdf_bytes = pdfkit.from_string(html_string, False, configuration=config)
    return pdf_bytes
