from django.contrib import admin

from .models import Player, Event, EventParticipation

admin.site.register(Player)
admin.site.register(Event)
admin.site.register(EventParticipation)
