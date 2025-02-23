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
        total_re_buy = Decimal('0.00')  # 🛠 Initialisieren der Gesamt-Re-Buys

        for player_id in selected_players:
            player = Player.objects.get(id=player_id)
            initial_buy_in_value = Decimal(request.POST.get(f'initial_buy_in_{player_id}', '0'))  # 🛠 Korrektur des Variablennamens

            # Überprüfen, ob der Spieler bereits eine EventParticipation hat
            existing_participation = EventParticipation.objects.filter(event=event, player=player).first()
            
            if existing_participation:
                # Falls es bereits ein initial_buy_in gibt, überspringen wir es beim Re-Buy
                if existing_participation.initial_buy_in > 0:
                    continue  # Wenn es bereits ein initial_buy_in gibt, überspringen wir diesen Spieler
                else:
                    # Falls es kein initial_buy_in gibt, dann ist es ein Re-Buy
                    re_buy_value = Decimal(request.POST.get(f're_buy_{player_id}', '0'))
                    existing_participation.re_buy = re_buy_value  # Setze den Re-Buy-Wert
                    existing_participation.save()
                    total_re_buy += re_buy_value  # Füge den Re-Buy zur Gesamtzahl hinzu
            else:
                # Erstelle EventParticipation mit initial buy-in value (nur beim ersten Mal)
                EventParticipation.objects.create(
                    event=event, 
                    player=player,
                    initial_buy_in=initial_buy_in_value if initial_buy_in_value > 0 else Decimal('0.00')  # Nur wenn der Wert > 0 ist
                )

                # Summe der Initial-Buy-Ins berechnen (nur für den ersten Buy-In)
                if initial_buy_in_value > 0:
                    total_initial_buy_in += initial_buy_in_value

        # Pot-Update: Subtrahiere die gesamten Initial Buy-Ins und Re-Buys
        event.remaining_chips -= (total_initial_buy_in + total_re_buy)
        event.save()

        # Redirect to home after adding players
        return redirect('home')

    return render(request, 'add_players.html', {
        'event': event,
        'players': players
    })




# View für Re-Buys (keine Initial Buy-Ins mehr)
def re_buy(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    participations = EventParticipation.objects.filter(event=event)

    # Formular-Set nur für 're_buy', kein 'initial_buy_in'
    ReBuyFormSet = modelformset_factory(
        EventParticipation,
        fields=('re_buy',),  # Nur das Re-Buy-Feld
        extra=0
    )

    if request.method == 'POST':
        print("POST-Daten:", request.POST)

        formset = ReBuyFormSet(request.POST, queryset=participations)

        if formset.is_valid():
            instances = formset.save(commit=False)
            print("Formset ist gültig, speichere Daten...")

            with transaction.atomic():
                total_re_buy = Decimal('0.00')

                for form in formset:
                    participation = form.save(commit=False)
                    re_buy = Decimal(form.cleaned_data.get('re_buy', '0.00'))  # Verhindert NoneType-Fehler

                    # Re-Buy nur speichern, wenn der Wert gesetzt wurde
                    if re_buy > Decimal('0.00'):
                        if event.remaining_chips < re_buy:
                            messages.error(request, "Nicht genügend Chips im Event für dieses Re-Buy!")
                            return redirect('re_buy', event_id=event.id)

                        total_re_buy += re_buy  # Summe der Re-Buys berechnen
                        participation.re_buy += re_buy  # Re-Buy zum bestehenden Wert hinzufügen
                        
                    participation.save()

                # Pot-Update nach allen Änderungen
                event.remaining_chips -= total_re_buy  # Remaining-Chips nach Re-Buys aktualisieren
                event.save()

            messages.success(request, "Re-Buy erfolgreich gespeichert!")  # Erfolgsmeldung
            return redirect('home')  # Weiterleitung zur Startseite

        else:
            messages.error(request, "Fehler beim Speichern der Re-Buys!")  # Fehler ausgeben
            print("Formset Fehler:", formset.errors)  # Debugging in der Konsole
            
    else:
        formset = ReBuyFormSet(queryset=participations)

    return render(request, 're_buy.html', {'formset': formset, 'event': event})

