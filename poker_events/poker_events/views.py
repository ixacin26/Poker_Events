from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q
from poker_data.models import Player, Event
from django.utils import timezone
from django.core.exceptions import ValidationError

# The following view calculates the necessary data for the ranking-cards in home.html
def home(request):
    # Fetch and sort players by total earnings for the "Top Poker Players Ranking"
    top_players = Player.objects.all().order_by('-total_earnings')
    
    # Fetch the last 3 events by date
    recent_events = Event.objects.order_by('-date')[:3]

    # Fetch players and calculate their earnings specifically for the last 3 events for the "Trend Poker Players Ranking"
    trend_players = (
        Player.objects.filter(event_participations__event__in=recent_events)
        .annotate(total_trend_earnings=Sum('event_participations__earnings', filter=Q(event_participations__event__in=recent_events)))
        .order_by('-total_trend_earnings')
    )

    # If no earnings exist for recent events, fall back to all-time top earnings
    if not trend_players.exists():
        trend_players = top_players

    # Fetch the active event(s) to display on the home page
    active_events = Event.objects.filter(active=True)

    # Check if any events are active
    active_events_exist = active_events.exists()

    # ASOP Ranking (All ASOP events)
    asop_players = (
        Player.objects.filter(event_participations__event__asop=True)
        .annotate(total_asop_earnings=Sum('event_participations__earnings'))
        .order_by('-total_asop_earnings')
    )

    # Last ASOP Ranking (Only the latest ASOP event)
    last_asop_event = Event.objects.filter(asop=True).order_by('-date').first()
    last_asop_players = (
        Player.objects.filter(event_participations__event=last_asop_event)
        .annotate(last_asop_earnings=Sum('event_participations__earnings'))
        .order_by('-last_asop_earnings')
    )

    # Render the home page with both player lists and active events
    return render(request, 'home.html', {
        'top_players': top_players,
        'trend_players': trend_players,
        'asop_players': asop_players,
        'last_asop_players': last_asop_players,
        'active_events_exist': active_events_exist,
        'active_events': active_events,  # Pass active events to the template
    })

# The following view defines the data for the add_event-template
def add_event(request):
    if request.method == 'POST':
        host_location = request.POST.get('host_location')
        date = request.POST.get('date')
        pot = request.POST.get('pot')
        active = request.POST.get('active') == 'on'
        asop = request.POST.get('asop') == 'on'

        # Create and save a new Event instance
        new_event = Event.objects.create(
            host_location=host_location,
            date=date,
            pot=pot,
            active=active,
            asop=asop
        )
        return redirect('home')  # TODO Redirect to home (or another page) after adding event

    return render(request, 'add_event.html')

# Receive the event ID
def end_event(request, event_id):
    # Get the event object
    event = get_object_or_404(Event, id=event_id)

    # Set the event as inactive
    event.active = False
    event.save()

    # Redirect back to the home page or to a page that shows all events
    return redirect('home')  # Adjust the URL name if necessary
