# Generated by Django 4.2.4 on 2023-09-25 20:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0008_station_alternative_tiploc'),
    ]

    operations = [
        migrations.AlterField(
            model_name='route',
            name='toc',
            field=models.ForeignKey(null='true', on_delete=django.db.models.deletion.SET_NULL, related_name='route_TOC_toc', to='timetable.toc'),
        ),
    ]
