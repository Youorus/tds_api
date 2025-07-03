from datetime import datetime
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
import phonenumbers

from api.models import Lead, LeadStatus, User, StatutDossier
from .Lead_status_serializer import LeadStatusSerializer
from .client_serializers import ClientSerializer
from .status_dossier_serializer import StatutDossierSerializer


class AssignedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email", "avatar")


class LeadSerializer(serializers.ModelSerializer):
    appointment_date = serializers.CharField(required=False, allow_null=True)
    form_data = ClientSerializer(read_only=True)
    assigned_to = AssignedUserSerializer(read_only=True)
    status = LeadStatusSerializer(read_only=True)
    statut_dossier = StatutDossierSerializer(read_only=True)

    # Ajout pour écrire depuis l’API
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

    class Meta:
        model = Lead
        fields = [
            'id', 'first_name', 'last_name', 'email',
            'phone', 'appointment_date', 'created_at',
            'form_data',
            'status', 'status_id',
            'assigned_to',
            'statut_dossier', 'statut_dossier_id',
        ]
        extra_kwargs = {
            'first_name': {'allow_blank': False},
            'last_name': {'allow_blank': False},
            'phone': {'allow_blank': False},
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
            parsed_number = phonenumbers.parse(value, None if value.startswith("+") else "FR")
            if not phonenumbers.is_valid_number(parsed_number):
                raise serializers.ValidationError(_("Le numéro de téléphone est invalide."))
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError(_("Le format du numéro de téléphone est incorrect."))

    def validate_appointment_date(self, value):
        if not value:
            return None
        try:
            parsed = datetime.strptime(value, "%d/%m/%Y %H:%M")
            parsed = timezone.make_aware(parsed)
        except ValueError:
            raise serializers.ValidationError(_("Format de date invalide. Utilisez JJ/MM/AAAA HH:mm."))
        if parsed < timezone.now():
            raise serializers.ValidationError(_("La date de rendez-vous ne peut pas être dans le passé."))
        if parsed.hour < 9 or (parsed.hour == 18 and parsed.minute > 30) or parsed.hour > 18:
            raise serializers.ValidationError(_("Les rendez-vous doivent être entre 9h et 18h30."))
        return parsed

    def validate(self, data):
        """Vérifie cohérence email, téléphone, statut et RDV."""
        email = data.get('email')
        phone = data.get('phone')
        status = data.get('status')  # via status_id
        appointment_date = data.get('appointment_date')
        instance = getattr(self, 'instance', None)

        if appointment_date is None and instance is not None:
            appointment_date = instance.appointment_date

        # On prend en compte le code ET le label (pour robustesse)
        status_code = getattr(status, "code", None)
        required_status = {"RDV_PLANIFIE", "RDV_CONFIRME"}

        # Si le statut nécessite un rendez-vous, la date doit être présente et valide
        if status_code and any(code in str(status_code).upper() for code in required_status):
            if not appointment_date:
                raise serializers.ValidationError({
                    "appointment_date": _(f"Une date de rendez-vous est requise pour ce statut «{status_code}».")
                })
            # La validation de date se fait déjà dans validate_appointment_date,
            # donc ici il suffit de s'assurer qu'elle soit présente.

        # Vérif numéro unique
        if phone:
            qs = Lead.objects.filter(phone=phone)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {'phone': _("Ce numéro de téléphone existe déjà. Veuillez nous contacter.")})

        # Vérif email unique
        if email:
            qs = Lead.objects.filter(email__iexact=email)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError({'email': _("Cet email existe déjà. Veuillez nous contacter.")})

        return data

    def create(self, validated_data):
        """Définit automatiquement le statut sur 'RDV_PLANIFIER' si un RDV est fourni sans statut."""
        if validated_data.get('appointment_date') and not validated_data.get('status'):
            try:
                validated_data['status'] = LeadStatus.objects.get(label__iexact="RDV_CONFIRME")
            except LeadStatus.DoesNotExist:
                pass  # laisse vide si le statut n’existe pas
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Applique seulement les changements explicitement demandés
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.appointment_date:
            rep['appointment_date'] = instance.appointment_date.strftime('%d/%m/%Y %H:%M')
        if instance.status:
            rep['status_display'] = instance.status.label
        return rep
