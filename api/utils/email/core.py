import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

def send_html_email(to_email, subject, template_name, context):
    """
    Envoie un email HTML à l'adresse fournie.
    - to_email: email du destinataire
    - subject: sujet
    - template_name: chemin du template HTML Django
    - context: contexte pour le rendu du template
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
    msg.send()
    logger.info(f"Email envoyé à {to_email} ({subject})")