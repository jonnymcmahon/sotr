from django.db import models

# Create your models here.


class Error(models.Model):
    timestamp = models.DateTimeField()
    stomp_msg = models.TextField()
    error_msg = models.TextField()