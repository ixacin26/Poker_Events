# Generated by Django 5.1.2 on 2024-10-20 11:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('host_location', models.CharField(blank=True, max_length=100, null=True)),
                ('pot', models.DecimalField(decimal_places=2, max_digits=10)),
                ('date', models.DateField()),
                ('active', models.BooleanField(default=True)),
                ('asop', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('founding_member', models.BooleanField(default=False)),
                ('first_participation', models.DateField(blank=True, null=True)),
                ('total_earnings', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='EventParticipation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('earnings', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='poker_data.event')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='poker_data.player')),
            ],
        ),
        migrations.AddField(
            model_name='event',
            name='host_player',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='hosted_events', to='poker_data.player'),
        ),
        migrations.AddField(
            model_name='event',
            name='participants',
            field=models.ManyToManyField(through='poker_data.EventParticipation', to='poker_data.player'),
        ),
    ]
