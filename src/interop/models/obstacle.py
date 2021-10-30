from django.db import models

class Obstacle(models.Model):
    # one to many
    mission = models.ForeignKey('UasMission', on_delete=models.CASCADE, null=True, blank=True)
    cylinder_height = models.FloatField()
    cylinder_radius = models.FloatField()
    latitude = models.FloatField()
    longitude = models.FloatField()
