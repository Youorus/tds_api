# api/utils/pdf/contract_generator.py

import pdfkit
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from api.contracts.models import Contract

def generate_contract_pdf(contract: Contract) -> bytes:
    """
    Génère le PDF du contrat à partir du template HTML et retourne les bytes.
    - contract : instance de Contract à convertir en PDF.
    - Retour : bytes du PDF généré (prêt à uploader sur MinIO/S3).
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
    config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_PATH) # ⬅️ Adapte selon ton serveur
    pdf_bytes = pdfkit.from_string(html_string, False, configuration=config)
    return pdf_bytes