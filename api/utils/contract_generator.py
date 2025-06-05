import pdfkit
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django.utils import timezone

from api.storage_backends import MinioReceiptStorage, MinioContractStorage


def generate_contract_pdf_sync(contract_data: dict) -> str:
    """
    Génère un contrat PDF à partir d'un template HTML et le stocke sur MinIO.
    `contract_data` doit contenir : first_name, last_name, phone, email, service, montant.
    """
    # Contexte pour le template HTML
    context = {
        "date": timezone.now().strftime("%d/%m/%Y"),
        "first_name": contract_data["first_name"],
        "last_name": contract_data["last_name"],
        "phone": contract_data["phone"],
        "email": contract_data["email"],
        "service": contract_data["service"],
        "montant": f"{contract_data['montant']:.2f}",
        "company": {
            "name": "TDS France",
            "email": "contact@tds-france.fr",
            "website": "www.tds-france.fr",
            "siret": "928 184 043",
            "logo_url": "https://i.imgur.com/iSzPCvI.jpeg",
        },
    }

    # Rendu du template HTML
    html_string = render_to_string("contrats/contract_template.html", context)

    # Configuration pdfkit (assurez-vous que wkhtmltopdf est installé sur le système)
    config = pdfkit.configuration(wkhtmltopdf="/usr/local/bin/wkhtmltopdf")  # adapte le chemin si besoin

    # Génération du PDF
    pdf_file = pdfkit.from_string(html_string, False, configuration=config)

    # Nom du fichier
    filename = f"contrat_{slugify(contract_data['last_name'])}_{slugify(contract_data['first_name'])}.pdf"

    # Sauvegarde dans MinIO
    file_content = ContentFile(pdf_file)
    storage = MinioContractStorage()
    saved_path = storage.save(filename, file_content)

    return storage.url(saved_path)