# Generated by Django 4.2.4 on 2023-09-21 13:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Station',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField()),
                ('crs', models.CharField()),
                ('tiploc', models.CharField()),
            ],
        ),
        migrations.CreateModel(
            name='Journey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('departureTime', models.TimeField(default='00:00:00')),
                ('arrivalTime', models.TimeField(default='00:00:00')),
                ('delayedTime', models.TimeField(default='00:00:00')),
                ('uid', models.CharField(default=0)),
                ('rid', models.CharField(default=0)),
                ('destination', models.ForeignKey(null='true', on_delete=django.db.models.deletion.SET_NULL, related_name='journey_destination', to='timetable.station')),
                ('origin', models.ForeignKey(null='true', on_delete=django.db.models.deletion.SET_NULL, related_name='journey_origin', to='timetable.station')),
            ],
        ),
    ]
