import pdfkit
from django.template.loader import render_to_string
from django.utils import timezone
from api.models import Contract

def generate_contract_pdf(contract: Contract) -> bytes:
    """
    Génère le PDF du contrat à partir du template HTML et retourne les bytes.
    """
    client = contract.client
    lead = client.lead

    context = {
        "date": timezone.now().strftime("%d/%m/%Y"),
        "first_name": lead.first_name,
        "last_name": lead.last_name,
        "phone": lead.phone,
        "email": lead.email,
        "service": contract.service,
        "montant": f"{contract.amount_due:.2f} €",
        "discount": f"{contract.discount_percent:.2f} %",
        "company": {
            "name": "TDS France",
            "email": "contact@tds-france.fr",
            "website": "www.tds-france.fr",
            "siret": "928 184 043",
            "logo_url": "https://i.imgur.com/iSzPCvI.jpeg",
        },
    }

    html_string = render_to_string("contrats/contract_template.html", context)
    config = pdfkit.configuration(wkhtmltopdf="/usr/local/bin/wkhtmltopdf")  # adapte le chemin si besoin
    pdf_bytes = pdfkit.from_string(html_string, False, configuration=config)
    return pdf_bytes

