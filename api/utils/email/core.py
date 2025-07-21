import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_html_email(
    to_email,
    subject,
    template_name,
    context,
    attachments=None
):
    """
    Envoie un email HTML à l'adresse fournie.
    - to_email: email du destinataire
    - subject: sujet
    - template_name: chemin du template HTML Django
    - context: contexte pour le rendu du template
    - attachments: liste de dicts {filename, content, mimetype} (optionnel)
    """
    if not to_email:
        logger.warning("Aucun email fourni.")
        return

    html_content = render_to_string(template_name, context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    msg.attach_alternative(html_content, "text/html")

    # Ajout des pièces jointes si présentes
    if attachments:
        for att in attachments:
            filename = att.get("filename")
            filecontent = att.get("content")
            mimetype = att.get("mimetype") or "application/pdf"
            if filename and filecontent:
                msg.attach(filename, filecontent, mimetype)
            else:
                logger.warning(f"Attachment ignoré (format incorrect): {att}")

    msg.send()