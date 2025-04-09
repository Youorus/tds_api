import logging
import pywhatkit
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self):
        self.browser_timeout = getattr(settings, 'WHATSAPP_BROWSER_TIMEOUT', 15)
        self.close_tab = getattr(settings, 'WHATSAPP_CLOSE_TAB', True)
        self.wait_time = getattr(settings, 'WHATSAPP_WAIT_TIME', 10)

    def _format_phone_number(self, phone_number: str) -> Optional[str]:
        """Formate le numéro de téléphone pour WhatsApp"""
        if not phone_number:
            return None

        cleaned = ''.join(c for c in phone_number if c.isdigit())

        if cleaned.startswith('0'):
            return f"+33{cleaned[1:]}"
        elif cleaned.startswith('33'):
            return f"+{cleaned}"
        elif cleaned.startswith('+'):
            return cleaned

        return None

    def send_message(self, phone_number: str, message: str) -> bool:
        """Envoie un message WhatsApp"""
        formatted_number = self._format_phone_number(phone_number)
        if not formatted_number:
            logger.error(f"Numéro de téléphone invalide: {phone_number}")
            return False

        try:
            pywhatkit.sendwhatmsg_instantly(
                phone_no=formatted_number,
                message=message,
                wait_time=self.wait_time,
                tab_close=self.close_tab,
                close_time=self.browser_timeout
            )
            logger.info(f"Message WhatsApp envoyé à {formatted_number}")
            return True
        except Exception as e:
            logger.error(f"Erreur WhatsApp pour {formatted_number}: {str(e)}")
            return False

    def send_appointment_confirmation(self, lead) -> bool:
        if not lead.phone:
            return False

        message = (
            f"Bonjour {lead.first_name},\n\n"
            f"Votre rendez-vous chez TDS France est confirmé pour le "
            f"{lead.get_formatted_appointment_date()} à "
            f"{lead.get_formatted_appointment_time()}.\n"
            f"Adresse: 11 rue de l'Arrivée, 75015 Paris\n\n"
            "À bientôt !\n"
            "L'équipe TDS France"
        )
        return self.send_message(lead.phone, message)

    def send_appointment_reminder(self, lead) -> bool:
        if not lead.phone:
            return False

        message = (
            f"Bonjour {lead.first_name},\n\n"
            f"Rappel: Vous avez rendez-vous demain à "
            f"{lead.get_formatted_appointment_time()}.\n"
            f"Adresse: 11 rue de l'Arrivée, 75015 Paris\n\n"
            "Cordialement,\n"
            "L'équipe TDS France"
        )
        return self.send_message(lead.phone, message)