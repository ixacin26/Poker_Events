# views.py
from django.shortcuts import render
from django.db.models import Sum
from poker_data.models import Player, Event

def home(request):
    # Fetch and sort players by total earnings for the "Top Poker Players Ranking"
    top_players = Player.objects.all().order_by('-total_earnings')
    
    # Fetch the last 3 events by date
    recent_events = Event.objects.order_by('-date')[:3]

    # Fetch players and their total earnings for only the last 3 events for the "Trend Poker Players Ranking"
    trend_players = (
        Player.objects.filter(event_participations__event__in=recent_events)
        .annotate(total_trend_earnings=Sum('event_participations__earnings'))
        .order_by('-total_trend_earnings')
    )

    # Render the home page with both player lists
    return render(request, 'home.html', {
        'top_players': top_players,
        'trend_players': trend_players,
    })
