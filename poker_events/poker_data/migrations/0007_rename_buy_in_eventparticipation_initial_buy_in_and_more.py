# Generated by Django 5.1.2 on 2025-02-23 08:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poker_data', '0006_event_remaining_chips'),
    ]

    operations = [
        migrations.RenameField(
            model_name='eventparticipation',
            old_name='buy_in',
            new_name='initial_buy_in',
        ),
        migrations.AddField(
            model_name='eventparticipation',
            name='re_buy',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
