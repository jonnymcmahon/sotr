# Generated by Django 4.2.4 on 2023-09-25 21:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0009_alter_route_toc'),
    ]

    operations = [
        migrations.AddField(
            model_name='route',
            name='num_stops',
            field=models.SmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='stop',
            name='stop_number',
            field=models.SmallIntegerField(),
        ),
    ]
