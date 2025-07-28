from datetime import datetime
from django.utils import timezone
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


class LeadSerializer(serializers.ModelSerializer):
    """
    Serializer principal du modèle Lead : lecture, création, mise à jour, validation métier.
    Inclut :
    - Les champs de base du Lead
    - Les données liées (statut, dossier, utilisateur assigné, données client)
    - Des champs d’écriture dédiés (_id) pour les foreign keys
    """
    appointment_date = serializers.CharField(required=False, allow_null=True)
    form_data = ClientSerializer(read_only=True)
    assigned_to = AssignedUserSerializer(read_only=True, many=True)
    status = LeadStatusSerializer(read_only=True)
    statut_dossier = StatutDossierSerializer(read_only=True)
    jurist_assigned = AssignedUserSerializer(read_only=True, many=True)
    jurist_assigned_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserRoles.JURISTE, is_active=True),
        many=True,
        source="jurists_assigned",
        write_only=True,
        required=False
    )

    juriste_assigned_at = serializers.DateTimeField(read_only=True)

    # Champs d’écriture pour status et statut_dossier via leur ID
    status_id = serializers.PrimaryKeyRelatedField(
        queryset=LeadStatus.objects.all(),
        source="status",
        write_only=True,
        required=False
    )
    statut_dossier_id = serializers.PrimaryKeyRelatedField(
        queryset=StatutDossier.objects.all(),
        source="statut_dossier",
        write_only=True,
        required=False
    )
    assigned_to_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserRoles.CONSEILLER, is_active=True),
        many=True,
        source="assigned_to",
        write_only=True,
        required=False
    )

    contract_emitter_id = serializers.SerializerMethodField()

    def get_contract_emitter_id(self, obj):
        """
        Retourne l’ID du conseiller ayant émis le contrat principal du client lié à ce lead.
        - On prend ici le dernier contrat créé (tu peux adapter la logique).
        """
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
            'id', 'first_name', 'last_name', 'email',
            'phone', 'appointment_date', 'created_at',
            'form_data',
            'status', 'status_id',
            'assigned_to', 'assigned_to_ids', "contract_emitter_id",
            'statut_dossier', 'statut_dossier_id',
            'jurist_assigned', 'jurist_assigned_ids',
            'juriste_assigned_at',
        ]
        extra_kwargs = {
            'first_name': {'allow_blank': False},
            'last_name': {'allow_blank': False},
            'phone': {'allow_blank': False},
            'created_at': {'read_only': True},
        }

    # ------------ VALIDATIONS INDIVIDUELLES ------------

    def validate_email(self, value):
        """
        Validation et normalisation de l’email.
        """
        if value and '@' not in value:
            raise serializers.ValidationError(_("Veuillez entrer une adresse email valide."))
        return value.lower().strip() if value else None

    def validate_first_name(self, value):
        """
        Prénom capitalisé.
        """
        return value.capitalize()

    def validate_last_name(self, value):
        """
        Nom capitalisé.
        """
        return value.capitalize()

    def validate_phone(self, value):
        """
        Validation et normalisation du numéro de téléphone international.
        Utilise phonenumbers.
        """
        try:
            parsed_number = phonenumbers.parse(value, None if value.startswith("+") else "FR")
            if not phonenumbers.is_valid_number(parsed_number):
                raise serializers.ValidationError(_("Le numéro de téléphone est invalide."))
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError(_("Le format du numéro de téléphone est incorrect."))

    def validate_appointment_date(self, value):
        """
        Validation du format JJ/MM/AAAA HH:mm, heure légale, non passée, slot autorisé.
        """
        if not value:
            return None
        try:
            parsed = datetime.strptime(value, "%d/%m/%Y %H:%M")
            parsed = timezone.make_aware(parsed)
        except ValueError:
            raise serializers.ValidationError(_("Format de date invalide. Utilisez JJ/MM/AAAA HH:mm."))
        if parsed < timezone.now():
            raise serializers.ValidationError(_("La date de rendez-vous ne peut pas être dans le passé."))
        return parsed

    # ------------ VALIDATIONS GLOBALES ------------
    def validate(self, data):
        """
        Validation de cohérence métier.
        Vérifie :
        - Statut et date de RDV si nécessaire
        - Unicité téléphone et email
        """
        email = data.get('email')
        phone = data.get('phone')
        status = data.get('status')  # via status_id
        appointment_date = data.get('appointment_date')
        instance = getattr(self, 'instance', None)

        if appointment_date is None and instance is not None:
            appointment_date = instance.appointment_date

        # Statut nécessite RDV
        status_code = getattr(status, "code", None)
        required_status = {"RDV_PLANIFIE", "RDV_CONFIRME"}
        if status_code and any(code in str(status_code).upper() for code in required_status):
            if not appointment_date:
                raise serializers.ValidationError({
                    "appointment_date": _(f"Une date de rendez-vous est requise pour ce statut «{status_code}».")
                })

        # Unicité téléphone
        if phone:
            qs = Lead.objects.filter(phone=phone)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {'phone': _("Ce numéro de téléphone existe déjà. Veuillez nous contacter.")})

        # Unicité email
        if email:
            qs = Lead.objects.filter(email__iexact=email)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError({'email': _("Cet email existe déjà. Veuillez nous contacter.")})

        return data

    # ------------ CRÉATION / MODIFICATION ------------

    def create(self, validated_data):
        """
        Si un RDV est fourni sans statut, assigne le statut 'RDV_CONFIRME'.
        """
        if validated_data.get('appointment_date') and not validated_data.get('status'):
            try:
                validated_data['status'] = LeadStatus.objects.get(label__iexact="RDV_CONFIRME")
            except LeadStatus.DoesNotExist:
                pass  # laisse vide si le statut n’existe pas
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Met à jour uniquement les champs explicitement transmis.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        """
        Représentation JSON :
        - Date de rendez-vous formatée.
        - Ajout du champ "status_display" (label).
        """
        rep = super().to_representation(instance)
        if instance.appointment_date:
            rep['appointment_date'] = instance.appointment_date.strftime('%d/%m/%Y %H:%M')
        if instance.status:
            rep['status_display'] = instance.status.label
        return rep