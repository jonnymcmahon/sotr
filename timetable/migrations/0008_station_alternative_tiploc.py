# Generated by Django 4.2.4 on 2023-09-25 16:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0007_rename_route_id_stop_route_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='station',
            name='alternative_tiploc',
            field=models.CharField(null=True),
        ),
    ]
