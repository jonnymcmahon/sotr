from django.db import models

# Create your models here.

class Station(models.Model):
    name = models.CharField()
    tiploc = models.CharField()
    alternative_tiploc = models.CharField(null=True)

class TOC(models.Model):
    name = models.CharField()
    toc = models.CharField()
    passengerSvc = models.BooleanField(default='False')

class Journey(models.Model):
    toc = models.ForeignKey(TOC, on_delete=models.SET_NULL, null='true', related_name='TOC_toc')
    origin = models.ForeignKey(Station, on_delete=models.SET_NULL, null='true', related_name='journey_origin')
    destination = models.ForeignKey(Station, on_delete=models.SET_NULL, null='true', related_name='journey_destination')
    date = models.DateField()
    departureTime = models.TimeField(default='00:00:00')
    arrivalTime = models.TimeField(default='00:00:00')
    delayedTime = models.IntegerField(default=0)
    uid = models.CharField(default=0)
    rid = models.CharField(default=0)

class Route(models.Model):
    orig = models.CharField(default=0)
    dest = models.CharField(default=0)
    num_stops = models.SmallIntegerField(default=0)
    toc = models.ForeignKey(TOC, on_delete=models.SET_NULL, null='true', related_name='route_TOC_toc')

class Stop(models.Model):
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null='true', related_name='Route_id')
    station = models.ForeignKey(Station, on_delete=models.SET_NULL, null='true', related_name='Station_name')
    stop_number = models.SmallIntegerField()
