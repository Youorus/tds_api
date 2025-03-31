from datetime import datetime

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
import phonenumbers

from api.models import Lead


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            'id', 'first_name', 'last_name', 'email',
            'phone', 'appointment_date',
            'status', 'assigned_to', 'created_at'
        ]
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'phone': {'required': True, 'allow_blank': False},
            'status': {'read_only': True},
            'created_at': {'read_only': True},
        }

    def validate_email(self, value):
        """Valide et normalise l'email."""
        if value and '@' not in value:
            raise serializers.ValidationError(
                _("Veuillez entrer une adresse email valide.")
            )
        return value.lower().strip() if value else None

    def validate_phone(self, value):
        """Valide et formate le numéro de téléphone en E.164."""
        if not value:
            raise serializers.ValidationError(_("Le numéro est obligatoire."))

        try:
            parsed = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError(_("Le numéro de téléphone est invalide."))
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError(_("Le format du numéro de téléphone est incorrect."))

    def validate_appointment_date(self, value):
        """Valide la date de rendez-vous."""
        if value and value < datetime.now().astimezone():
            raise serializers.ValidationError(_("La date de rendez-vous ne peut pas être dans le passé."))
        if value and (value.hour < 9 or (value.hour == 18 and value.minute > 30) or value.hour > 18):
            raise serializers.ValidationError(_("Les rendez-vous doivent être entre 9h et 18h30."))
        return value

    def validate(self, data):
        """Vérifie l'unicité du téléphone et de l'email."""
        email = data.get('email')
        phone = data.get('phone')
        instance = getattr(self, 'instance', None)

        if phone:
            queryset = Lead.objects.filter(phone=phone)
            if instance:
                queryset = queryset.exclude(pk=instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({'phone': _("Un lead avec ce numéro de téléphone existe déjà.")})

        if email:
            queryset = Lead.objects.filter(email__iexact=email)
            if instance:
                queryset = queryset.exclude(pk=instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({'email': _("Un lead avec cet email existe déjà.")})

        return data

    def create(self, validated_data):
        """Définit automatiquement le statut sur RDV_CONFIRME si un rendez-vous est ajouté."""
        if validated_data.get('appointment_date'):
            validated_data['status'] = Lead.LeadStatus.RDV_CONFIRME
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Met à jour le statut si un rendez-vous est ajouté à un lead NOUVEAU."""
        instance = super().update(instance, validated_data)
        if instance.appointment_date and instance.status == Lead.LeadStatus.NOUVEAU:
            instance.status = Lead.LeadStatus.RDV_CONFIRME
            instance.save()
        return instance

    def to_representation(self, instance):
        """Formate les données pour la réponse API."""
        representation = super().to_representation(instance)

        representation['status_display'] = instance.get_status_display()

        if instance.appointment_date:
            representation['appointment_date'] = instance.appointment_date.strftime('%d/%m/%Y %H:%M')

        if instance.assigned_to:
            representation['assigned_to'] = {
                'id': instance.assigned_to.id,
                'name': instance.assigned_to.get_full_name(),
                'email': instance.assigned_to.email
            }

        return representation