from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum

class Player(models.Model):
    # Add logic for an inactive player
    name = models.CharField(max_length=100)
    founding_member = models.BooleanField(default=False)
    first_participation = models.DateField(blank=True, null=True)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def update_total_earnings(self):
        # Update total_earnings based on all related EventParticipation instances
        self.total_earnings = self.event_participations.aggregate(total=Sum('earnings'))['total'] or 0
        self.save()

    def __str__(self):
        return self.name

class Event(models.Model):
    host_location = models.CharField(max_length=100, blank=True, null=True)  # formerly "gastgeber_ort"
    participants = models.ManyToManyField(Player, through='EventParticipation', related_name='events')  # formerly "teilnehmer"
    pot = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()  # formerly "datum" #TODO change format to dd.mm.yyyy
    active = models.BooleanField(default=True)  # formerly "active"
    asop = models.BooleanField(default=False)  # formerly "asop"
    host_player = models.ForeignKey(Player, on_delete=models.SET_NULL, blank=True, null=True, related_name='hosted_events')  # formerly "gastgeber_spieler"

    def clean(self):
        # Custom validation to ensure either `asop` is True or `gastgeber_spieler` is provided
        if not self.asop and not self.host_player:
            raise ValidationError("Entweder muss ASOP aktiviert sein oder ein Spieler ausgewählt werden.")
        elif self.asop and self.host_player:
            raise ValidationError("Entweder ASOP aktivieren oder einen Spieler auswählen, aber nicht beides.")
        elif not self.asop and self.host_player is None:
            raise ValidationError("Wenn ASOP nicht aktiviert ist, muss ein Gastgeber-Spieler ausgewählt werden.")

    def __str__(self):
        return f"Event on {self.date} with Pot: {self.pot}"


class EventParticipation(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='event_participations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    buy_in = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # New buy-in field

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the player's total earnings whenever an EventParticipation is saved
        self.player.update_total_earnings()

    def __str__(self):
        return f"{self.player.name} in {self.event.date}"