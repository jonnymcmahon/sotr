# Generated by Django 4.2.4 on 2023-10-03 14:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0010_route_num_stops_alter_stop_stop_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='route',
            name='checksum',
            field=models.CharField(null='true'),
            preserve_default='true',
        ),
    ]
