from rest_framework import serializers
from django.contrib.auth import get_user_model

from api.jurist_availability_date.models import JuristGlobalAvailability

User = get_user_model()


class JuristBasicSerializer(serializers.ModelSerializer):
    """Serializer de base pour les juristes"""

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'avatar']
        read_only_fields = fields


class JuristGlobalAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer pour les disponibilités des juristes"""

    jurist_details = JuristBasicSerializer(source='jurist', read_only=True)
    time_slots = serializers.SerializerMethodField()

    class Meta:
        model = JuristGlobalAvailability
        fields = [
            'id',
            'availability_type',
            'jurist',
            'jurist_details',
            'date',
            'start_time',
            'end_time',
            'slot_duration',
            'repeat_weekly',
            'is_active',
            'time_slots',
            'duration_minutes',
            'available_slots_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_time_slots(self, obj):
        """Inclut les créneaux horaires si demandé"""
        if self.context.get('include_slots', False):
            return obj.get_time_slots()
        return None

    def validate(self, data):
        """Validation personnalisée"""
        availability_type = data.get('availability_type')
        jurist = data.get('jurist')

        # Validation : juriste requis si type spécifique
        if availability_type == 'specific' and not jurist:
            raise serializers.ValidationError({
                'jurist': "Un juriste doit être sélectionné pour une disponibilité spécifique"
            })

        # Validation : pas de juriste si type global
        if availability_type == 'global' and jurist:
            raise serializers.ValidationError({
                'jurist': "Aucun juriste ne doit être sélectionné pour une disponibilité globale"
            })

        # Validation : heure de fin après heure de début
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({
                'end_time': "L'heure de fin doit être après l'heure de début"
            })

        return data


class AvailabilityStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques de disponibilités"""

    total_availabilities = serializers.IntegerField()
    global_availabilities = serializers.IntegerField()
    specific_availabilities = serializers.IntegerField()
    total_slots = serializers.IntegerField()
    active_jurists = serializers.IntegerField()