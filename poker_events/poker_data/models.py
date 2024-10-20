from django.db import models

class Player(models.Model):
    name = models.CharField(max_length=100)
    founding_member = models.BooleanField(default=False)  # formerly "Gründungsmitglied"
    first_participation = models.DateField(blank=True, null=True)  # formerly "Erste Teilnahme"
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # formerly "gesamtgewinn"

    def __str__(self):
        return self.name

class Event(models.Model):
    host_location = models.CharField(max_length=100, blank=True, null=True)  # formerly "gastgeber_ort"
    participants = models.ManyToManyField(Player, through='EventParticipation')  # formerly "teilnehmer"
    pot = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()  # formerly "datum"
    active = models.BooleanField(default=True)  # formerly "active"
    asop = models.BooleanField(default=False)  # formerly "asop"
    host_player = models.ForeignKey(Player, on_delete=models.SET_NULL, blank=True, null=True, related_name='hosted_events')  # formerly "gastgeber_spieler"

    def clean(self):
        if not self.asop and not self.host_player:
            raise ValidationError("Either a host player or ASOP event must be provided.")

    def __str__(self):
        return f"Event on {self.date} with Pot: {self.pot}"


class EventParticipation(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)  # formerly "spieler"
    event = models.ForeignKey(Event, on_delete=models.CASCADE)  # formerly "event"
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # formerly "eventgewinn"

    def __str__(self):
        return f"{self.player.name} in {self.event.date}"