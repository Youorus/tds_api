from datetime import datetime

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
import phonenumbers

from api.models import Lead, LeadStatus


class LeadSerializer(serializers.ModelSerializer):
    appointment_date = serializers.CharField(required=False, allow_null=True)
    class Meta:
        model = Lead
        fields = [
            'id', 'first_name', 'last_name', 'email',
            'phone', 'appointment_date',
            'status', 'assigned_to', 'created_at'
        ]
        extra_kwargs = {
            'first_name': {'allow_blank': False},
            'last_name': {'allow_blank': False},
            'phone': {'allow_blank': False},
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
        try:
            # 📌 Si le numéro ne commence pas par "+", on assume que c'est un numéro FR
            parsed_number = phonenumbers.parse(value, None if value.startswith("+") else "FR")

            # ✅ Vérifie si le numéro est valide
            if not phonenumbers.is_valid_number(parsed_number):
                raise serializers.ValidationError(_("Le numéro de téléphone est invalide."))

            # ✅ Retourne le numéro au format international standard (ex: +33612345678)
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)

        except phonenumbers.NumberParseException:
            raise serializers.ValidationError(_("Le format du numéro de téléphone est incorrect."))

    def validate_appointment_date(self, value):
        if not value:
            return None

        try:
            parsed = datetime.strptime(value, "%d/%m/%Y %H:%M")
            parsed = timezone.make_aware(parsed)  # <-- Corrige le problème
        except ValueError:
            raise serializers.ValidationError(
                _("Format de date invalide. Utilisez JJ/MM/AAAA HH:mm.")
            )

        if parsed < timezone.now():  # ✅ Comparaison entre deux datetimes aware
            raise serializers.ValidationError(_("La date de rendez-vous ne peut pas être dans le passé."))

        if parsed.hour < 9 or (parsed.hour == 18 and parsed.minute > 30) or parsed.hour > 18:
            raise serializers.ValidationError(_("Les rendez-vous doivent être entre 9h et 18h30."))

        return parsed

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
                raise serializers.ValidationError({'phone': _("Ce numéro de téléphone existe déjà. Veuillez nous Contacter")})

        if email:
            queryset = Lead.objects.filter(email__iexact=email)
            if instance:
                queryset = queryset.exclude(pk=instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({'email': _("cet email existe déjà. Veuillez nous Contacter")})

        return data

    def create(self, validated_data):
        """Définit automatiquement le statut sur RDV_PLANIFIER uniquement si aucun statut n'est fourni."""
        if validated_data.get('appointment_date') and not validated_data.get('status'):
            validated_data['status'] = LeadStatus.RDV_PLANIFIER
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Met à jour un lead sans logique métier automatique."""
        return super().update(instance, validated_data)

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