# Generated by Django 4.2.4 on 2023-10-07 10:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0016_delay'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stop',
            name='route',
            field=models.ForeignKey(null='true', on_delete=django.db.models.deletion.CASCADE, related_name='Route_id', to='timetable.route'),
        ),
        migrations.AlterField(
            model_name='stop',
            name='station',
            field=models.ForeignKey(null='true', on_delete=django.db.models.deletion.CASCADE, related_name='Station_name', to='timetable.station'),
        ),
    ]
