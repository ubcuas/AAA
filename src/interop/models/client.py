from django.db import models

class ClientSession(models.Model):
    """
    """
    username = models.CharField(max_length=256, blank=True)
    password = models.CharField(max_length=256, blank=True)

    url = models.CharField(max_length=256, blank=True)
    session_id = models.CharField(max_length=256, blank=True)

    expires = models.DateTimeField(null=True)
    created = models.DateTimeField(null=True)
    active = models.BooleanField(default=False)

class Connected(models.Model):
    """
    This model is just to sync if we are connected to the drone
    """
    connected = models.BooleanField(default=False)
