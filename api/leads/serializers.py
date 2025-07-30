from datetime import datetime
from zoneinfo import ZoneInfo
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
import phonenumbers

from api.lead_status.models import LeadStatus
from api.lead_status.serializer import LeadStatusSerializer
from api.clients.serializers import ClientSerializer
from api.leads.models import Lead
from api.statut_dossier.models import StatutDossier
from api.statut_dossier.serializers import StatutDossierSerializer
from api.users.assigned_user_serializer import AssignedUserSerializer
from api.users.models import User
from api.users.roles import UserRoles

# Fuseau horaire par défaut (zoneinfo)
EUROPE_PARIS = ZoneInfo("Europe/Paris")

class LeadSerializer(serializers.ModelSerializer):
    appointment_date = serializers.DateTimeField(
        input_formats=['%d/%m/%Y %H:%M'],    # format reçu du front
        default_timezone=EUROPE_PARIS,       # on l’interprète en Europe/Paris
        format='%d/%m/%Y %H:%M',             # même chaîne renvoyée au front
        allow_null=True,
        required=False,
    )
    form_data = ClientSerializer(read_only=True)
    assigned_to = AssignedUserSerializer(read_only=True, many=True)
    status = LeadStatusSerializer(read_only=True)
    statut_dossier = StatutDossierSerializer(read_only=True)
    jurist_assigned = AssignedUserSerializer(read_only=True, many=True)
    jurist_assigned_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserRoles.JURISTE, is_active=True),
        many=True, source="jurist_assigned", write_only=True, required=False
    )

    status_id = serializers.PrimaryKeyRelatedField(
        queryset=LeadStatus.objects.all(), source="status", write_only=True, required=False
    )
    statut_dossier_id = serializers.PrimaryKeyRelatedField(
        queryset=StatutDossier.objects.all(), source="statut_dossier", write_only=True, required=False
    )
    assigned_to_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserRoles.CONSEILLER, is_active=True),
        many=True, source="assigned_to", write_only=True, required=False
    )

    contract_emitter_id = serializers.SerializerMethodField()

    def get_contract_emitter_id(self, obj):
        client = getattr(obj, 'form_data', None)
        if not client:
            return None
        contract = client.contracts.order_by('-created_at').first()
        if contract and contract.created_by:
            return str(contract.created_by.id)
        return None

    class Meta:
        model = Lead
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone',
            'appointment_date', 'created_at',
            'form_data', 'status', 'status_id',
            'assigned_to', 'assigned_to_ids', 'contract_emitter_id',
            'statut_dossier', 'statut_dossier_id',
            'jurist_assigned', 'jurist_assigned_ids',
        ]
        extra_kwargs = {
            'first_name': {'allow_blank': False},
            'last_name':  {'allow_blank': False},
            'phone':      {'allow_blank': False},
            'created_at': {'read_only': True},
        }

    def validate_email(self, value):
        if value and '@' not in value:
            raise serializers.ValidationError(_("Veuillez entrer une adresse email valide."))
        return value.lower().strip() if value else None

    def validate_first_name(self, value):
        return value.capitalize()

    def validate_last_name(self, value):
        return value.capitalize()

    def validate_phone(self, value):
        try:
            parsed = phonenumbers.parse(value, None if value.startswith('+') else 'FR')
            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError(_("Le numéro est invalide."))
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError(_("Format du numéro incorrect."))

    def validate(self, data):
        # logique métier (statut vs appointment_date, unicité, etc.)
        return super().validate(data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.appointment_date:
            # Convertit l'UTC stockée en Europe/Paris
            paris_dt = instance.appointment_date.astimezone(EUROPE_PARIS)
            rep['appointment_date'] = paris_dt.strftime('%d/%m/%Y %H:%M')
        if instance.status:
            rep['status_display'] = instance.status.label
        return rep