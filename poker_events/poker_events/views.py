from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from django.db.models import Sum, Q
from django.db import transaction
from poker_data.models import Player, Event, EventParticipation
from django.utils import timezone
from django.core.exceptions import ValidationError

# The following view calculates the necessary data for home.html
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

    # Fetch the players for each active event
    for event in active_events:
        event.players = event.eventparticipation_set.all()  # Get players associated with the event

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

def add_event(request):
    event_created = False  # Flag to track if the event was created

    if request.method == 'POST':
        host_location = request.POST.get('host_location')
        date = request.POST.get('date')
        pot = request.POST.get('pot')
        active = request.POST.get('active') == 'on'
        asop = request.POST.get('asop') == 'on'
        host_player_id = request.POST.get('host_player')

        # Fetch the selected host player
        host_player = Player.objects.get(id=host_player_id) if host_player_id else None

        # Create and save a new Event instance
        new_event = Event.objects.create(
            host_location=host_location,
            date=date,
            pot=pot,
            active=active,
            asop=asop,
            host_player=host_player
        )
        
        event_created = True  # Set the flag to True when the event is created

        # Redirect to the page for adding players to the event
        return redirect('add_players', event_id=new_event.id)  # Redirect to the add_players page

    # Fetch all players to display in the dropdown
    players = Player.objects.all()

    return render(request, 'add_event.html', {
        'players': players,
        'event_created': event_created  # Pass the flag to the template
    })

# Receive the event ID
def end_event(request, event_id):
    # Get the event object
    event = get_object_or_404(Event, id=event_id)

    # Set the event as inactive
    event.active = False
    event.save()

    # Redirect back to the home page or to a page that shows all events
    return redirect('home')  # Adjust the URL name if necessary

# add players to a recently created event
def add_players(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    players = Player.objects.all()

    if request.method == 'POST':
        # Überprüfen, ob der "Cancel"-Button geklickt wurde
        if 'cancel' in request.POST:
            event.delete()  # Lösche den Event
            return redirect('home')  # Weiterleitung zur Startseite

        # Spieler hinzufügen, wenn der "Cancel"-Button nicht geklickt wurde
        selected_players = request.POST.getlist('players')  # Get selected players from the form
        for player_id in selected_players:
            player = Player.objects.get(id=player_id)
            buy_in_value = request.POST.get(f'buy_in_{player_id}', 0)  # Get the buy-in value for the Player

            # Create EventParticipation with buy-in value
            EventParticipation.objects.create(
                event=event, 
                player=player,
                buy_in=buy_in_value  # Set the buy-in value for the player
            )

        # Redirect to home after adding players
        return redirect('home')

    return render(request, 'add_players.html', {
        'event': event,
        'players': players
    })

#View for buy_in in the beginning of an event as well as for re-buys
def buy_in(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    participations = EventParticipation.objects.filter(event=event)

    # Create a modelformset for EventParticipation
    BuyInFormSet = modelformset_factory(
        EventParticipation,
        fields=('buy_in',),
        extra=0  # No extra empty forms
    )

    if request.method == 'POST':
        formset = BuyInFormSet(request.POST, queryset=participations)
        if formset.is_valid():
            with transaction.atomic():
                # Update the buy_in field for each player and adjust the event's pot
                for form in formset:
                    participation = form.save(commit=False)
                    event.pot -= participation.buy_in  # Subtract buy-in from event pot
                    participation.save()
                event.save()

            return redirect('home')  # Redirect to home after saving

    else:
        formset = BuyInFormSet(queryset=participations)

    return render(request, 'buy_in.html', {'formset': formset, 'event': event})
