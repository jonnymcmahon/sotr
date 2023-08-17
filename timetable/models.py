from django.db import models

# Create your models here.

class Station(models.Model):
    name = models.CharField()
    crs = models.CharField()
    tiploc = models.CharField()

class Journey(models.Model):
    origin = models.ForeignKey(Station, on_delete=models.SET_NULL, null='true', related_name='journey_origin')
    destination = models.ForeignKey(Station, on_delete=models.SET_NULL, null='true', related_name='journey_destination')
    date = models.DateField()
    departureTime = models.TimeField(default='00:00:00')
    arrivalTime = models.TimeField(default='00:00:00')
    delayedTime = models.IntegerField(default=0)
    uid = models.CharField(default=0)