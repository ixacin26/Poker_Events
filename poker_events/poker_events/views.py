from django.shortcuts import render, redirect
from django.db.models import Sum, Q
from poker_data.models import Player, Event
from django.utils import timezone

#The following view calculates the necessary data for the ranking-cards in home.html
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

    #TODO add "Latest ASOP Ranking"

    # Render the home page with both player lists
    return render(request, 'home.html', {
        'top_players': top_players,
        'trend_players': trend_players,
    })

#The following view defines the data for the add_event-template
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
