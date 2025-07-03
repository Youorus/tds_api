from rest_framework import serializers
from django.utils import timezone
from api.models import Client, Service
from api.serializers.service_serializer import ServiceSerializer


class ClientSerializer(serializers.ModelSerializer):
    # Champ write-only pour la MAJ (id)
    type_demande_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        source="type_demande",
        write_only=True,
        required=False,
        allow_null=True,
    )
    # Champ read-only pour l'affichage (objet détaillé)
    type_demande = ServiceSerializer(read_only=True)
    class Meta:
        model = Client
        exclude = ["lead"]

    # --- Champs individuels ---

    def validate_date_naissance(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("La date de naissance ne peut pas être dans le futur.")
        return value

    def validate_date_entree_france(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("La date d’entrée en France ne peut pas être dans le futur.")
        return value

    def validate_date_depuis_sans_emploi(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("La date ne peut pas être dans le futur.")
        return value

    def validate_date_derniere_oqtf(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("La date ne peut pas être dans le futur.")
        return value

    def validate_code_postal(self, value):
        if not value.isdigit() or not (4 <= len(value) <= 5):
            raise serializers.ValidationError("Le code postal doit contenir 4 ou 5 chiffres.")
        return value

    def validate_adresse(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("L'adresse est trop courte (minimum 5 caractères).")
        return value

    def validate_ville(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Le nom de la ville est trop court.")
        return value

    def validate_remarques(self, value):
        if value and len(value) > 255:
            raise serializers.ValidationError("Maximum 255 caractères autorisés.")
        return value

    def validate_demande_formulee_precise(self, value):
        if value and len(value) > 255:
            raise serializers.ValidationError("Maximum 255 caractères autorisés.")
        return value

    def validate_services(self, value):
        if not value:
            raise serializers.ValidationError("Veuillez sélectionner au moins un service.")
        return value


    def validate_type_demande(self, value):
        if not value:
            raise serializers.ValidationError("Veuillez sélectionner un type de demande.")
        return value
    # --- Validation croisée ---

    def validate(self, data):
        errors = {}
        is_partial = self.partial

        if (not is_partial or 'type_visa' in data) and data.get('a_un_visa') and not data.get('type_visa'):
            errors['type_visa'] = "Veuillez sélectionner un type de visa"

        if (not is_partial or 'domaine_activite' in data) and data.get('situation_pro') and not data.get(
                'domaine_activite'):
            errors['domaine_activite'] = "Veuillez indiquer votre domaine d’activité"

        if (not is_partial or 'nombre_enfants' in data) and data.get('nombre_enfants') is not None and data[
            'nombre_enfants'] < 0:
            errors['nombre_enfants'] = "Veuillez saisir un nombre valide"

        if (not is_partial or 'nombre_enfants_francais' in data) and data.get('nombre_enfants_francais') is not None and \
                data['nombre_enfants_francais'] < 0:
            errors['nombre_enfants_francais'] = "Veuillez saisir un nombre valide"

        if (not is_partial or 'nombre_fiches_paie' in data) and data.get('nombre_fiches_paie') is not None and data[
            'nombre_fiches_paie'] < 0:
            errors['nombre_fiches_paie'] = "Veuillez saisir un nombre valide"

        if errors:
            raise serializers.ValidationError(errors)

        return data