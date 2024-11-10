# poker_data/context_processors.py
from poker_data.models import Event

def active_events_status(request):
    return {
        'active_events_exist': Event.objects.filter(active=True).exists()
    }
