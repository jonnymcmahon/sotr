# Generated by Django 4.2.4 on 2023-09-21 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='journey',
            name='delayedTime',
            field=models.IntegerField(default=0),
        ),
    ]