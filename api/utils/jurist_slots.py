from datetime import datetime, timedelta

from django.utils.timezone import get_current_timezone, make_aware

from api.jurist_availability_date.models import JuristGlobalAvailability

SLOT_DURATION = timedelta(minutes=30)


def is_valid_day(day):
    """
    Retourne True si au moins une plage globale existe ce jour-là.
    """
    return JuristGlobalAvailability.objects.filter(day_of_week=day.weekday()).exists()


def get_slots_for_day(day):
    """
    Retourne TOUS les créneaux (aware, Europe/Paris) pour le jour donné,
    dynamiquement selon les JuristGlobalAvailability.
    """

    tz = get_current_timezone()  # Toujours Europe/Paris si settings correct
    slots = []

    availabilities = JuristGlobalAvailability.objects.filter(day_of_week=day.weekday())
    for avail in availabilities:
        hstart, hend = avail.start_time, avail.end_time
        current = datetime.combine(day, hstart)
        end_dt = datetime.combine(day, hend)
        # Boucle sur la plage, intervalle 30 min
        while current + SLOT_DURATION <= end_dt:
            aware_slot = make_aware(current, timezone=tz)
            slots.append(aware_slot)
            current += SLOT_DURATION
    return slots


def get_available_slots_for_jurist(jurist, day):
    """
    Retourne les créneaux disponibles (au format ISO string) pour ce juriste et ce jour,
    selon les plages globales.
    """
    from api.jurist_appointment.models import JuristAppointment

    all_slots = get_slots_for_day(day)
    taken = set(
        JuristAppointment.objects.filter(jurist=jurist, date__date=day).values_list(
            "date", flat=True
        )
    )
    available = [slot for slot in all_slots if slot not in taken]
    return [slot.isoformat() for slot in available]
