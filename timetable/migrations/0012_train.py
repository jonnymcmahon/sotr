# Generated by Django 4.2.4 on 2023-10-04 19:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0011_route_checksum'),
    ]

    operations = [
        migrations.CreateModel(
            name='Train',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(null='true')),
                ('rid', models.CharField(default=0)),
                ('cancelled', models.BooleanField(null='true')),
                ('route', models.ForeignKey(null='true', on_delete=django.db.models.deletion.CASCADE, related_name='train_route_id', to='timetable.route')),
                ('toc', models.ForeignKey(null='true', on_delete=django.db.models.deletion.SET_NULL, related_name='train_toc_id', to='timetable.toc')),
            ],
        ),
    ]
