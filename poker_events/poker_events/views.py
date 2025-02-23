from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from django.db.models import Sum, Q
from django.db import transaction
from poker_data.models import Player, Event, EventParticipation
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib import messages
from decimal import Decimal

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

        for participation in event.players:
            participation.total_buy_in = participation.initial_buy_in + participation.re_buy  # 🛠 Summe aus Initial + Re-Buys

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
            host_player=host_player,
            remaining_chips=pot  # 🛠 Initialisiere die verbleibenden Chips mit dem Pot-Wert
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
        
        total_initial_buy_in = Decimal('0.00')  # 🛠 Initialisieren der Gesamt-Buy-Ins

        for player_id in selected_players:
            player = Player.objects.get(id=player_id)
            initial_buy_in_value = Decimal(request.POST.get(f'initial_buy_in_{player_id}', '0'))  # 🛠 Korrektur des Variablennamens

            # Create EventParticipation with initial buy-in value
            EventParticipation.objects.create(
                event=event, 
                player=player,
                initial_buy_in=initial_buy_in_value  # 🛠 Korrektes Feld
            )

            total_initial_buy_in += initial_buy_in_value  # 🛠 Summe der Initial-Buy-Ins berechnen

        # 🛠 Pot-Update: Subtrahiere die gesamten Initial Buy-Ins
        event.pot -= total_initial_buy_in
        event.save()

        # Redirect to home after adding players
        return redirect('home')

    return render(request, 'add_players.html', {
        'event': event,
        'players': players
    })


# View for buy_in in the beginning of an event as well as for re-buys
def buy_in(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    participations = EventParticipation.objects.filter(event=event)

    BuyInFormSet = modelformset_factory(
        EventParticipation,
        fields=('initial_buy_in', 're_buy',),  # Korrektur: Wir bearbeiten nur initial_buy_in und re_buy!
        extra=0
    )

    if request.method == 'POST':
        print("POST-Daten:", request.POST)

        formset = BuyInFormSet(request.POST, queryset=participations)

        if formset.is_valid():
            instances = formset.save(commit=False)
            print("Formset ist gültig, speichere Daten...")

            with transaction.atomic():
                total_initial_buy_in = Decimal('0.00')
                total_re_buy = Decimal('0.00')

                for form in formset:
                    participation = form.save(commit=False)
                    initial_buy_in = Decimal(form.cleaned_data.get('initial_buy_in', '0.00'))  # Verhindert NoneType-Fehler
                    re_buy = Decimal(form.cleaned_data.get('re_buy', '0.00'))  # Verhindert NoneType-Fehler

                    # Initial Buy-In nur speichern, wenn der Wert gesetzt wurde
                    if initial_buy_in > Decimal('0.00') and participation.initial_buy_in == 0:
                        participation.initial_buy_in = initial_buy_in
                        total_initial_buy_in += initial_buy_in  # Summe des Initial-Buy-In berechnen

                    # Re-Buy nur speichern, wenn der Wert gesetzt wurde
                    if re_buy > Decimal('0.00'):
                        if event.remaining_chips < re_buy:
                            messages.error(request, "Nicht genügend Chips im Event für dieses Re-Buy!")
                            return redirect('buy_in', event_id=event.id)

                        total_re_buy += re_buy  # Summe der Re-Buys berechnen
                        participation.re_buy += re_buy  # Re-Buy zum bestehenden Wert hinzufügen
                        
                    participation.save()

                # Pot-Update nach allen Änderungen
                event.pot -= total_initial_buy_in + total_re_buy  # Pot wird um Initial-Buy-In und Re-Buys reduziert
                event.remaining_chips -= total_re_buy  # Remaining-Chips nach Re-Buys aktualisieren
                event.save()

            messages.success(request, "Buy-In und/oder Re-Buy erfolgreich gespeichert!")  # Erfolgsmeldung
            return redirect('home')  # Weiterleitung zur Startseite

        else:
            messages.error(request, "Fehler beim Speichern der Buy-Ins und Re-Buys!")  # Fehler ausgeben
            print("Formset Fehler:", formset.errors)  # Debugging in der Konsole
            

    else:
        formset = BuyInFormSet(queryset=participations)

    return render(request, 'buy_in.html', {'formset': formset, 'event': event})

