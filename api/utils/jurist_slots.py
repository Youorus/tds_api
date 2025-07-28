from datetime import datetime, timedelta, time
from django.utils.timezone import make_aware, get_current_timezone

SLOT_DURATION = timedelta(minutes=30)
TUESDAY = 1
THURSDAY = 3

def is_valid_day(day):
    return day.weekday() in [TUESDAY, THURSDAY]

def get_slots_for_day(day):
    """
    Retourne TOUS les créneaux (aware, Europe/Paris) pour le jour donné (mardi/jeudi)
    """
    tz = get_current_timezone()  # Toujours Europe/Paris si settings correct
    slots = []
    if day.weekday() == TUESDAY:
        hstart, hend = time(10, 30), time(13, 30)
    elif day.weekday() == THURSDAY:
        hstart, hend = time(14, 30), time(18, 0)
    else:
        return slots

    current = datetime.combine(day, hstart)
    end_dt = datetime.combine(day, hend)
    while current <= end_dt:
        # Rends l'objet aware en Europe/Paris !
        aware_slot = make_aware(current, timezone=tz)
        slots.append(aware_slot)
        current += SLOT_DURATION
    return slots

def get_available_slots_for_jurist(jurist, day):
    """
    Retourne les créneaux disponibles (au format ISO string) pour ce juriste et ce jour.
    """
    from api.jurist_appointment.models import JuristAppointment
    all_slots = get_slots_for_day(day)
    taken = set(
        JuristAppointment.objects.filter(jurist=jurist, date__date=day)
        .values_list("date", flat=True)
    )
    available = [slot for slot in all_slots if slot not in taken]
    return [slot.isoformat() for slot in available]