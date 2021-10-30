from django.db import models


# OrderedWayPoint is used as the Mission waypoints
class OrderedWayPoint(models.Model):
    # One to many relationship
    mission = models.ForeignKey('UasMission', on_delete=models.CASCADE)
    altitude_msl = models.FloatField(null= True, default= 200.0)
    latitude = models.FloatField()
    longitude = models.FloatField()
    order = models.IntegerField()

    class Meta:
        unique_together = (("mission", "order"),)


"""
UAS Flyzone Ordered Boundary Points
"""
class OrderedBoundaryPoint(models.Model):
    # self-determined primary key
    latitude = models.FloatField()
    longitude = models.FloatField()
    order = models.IntegerField(db_index=True)
    fly_zone = models.ForeignKey('FlyZone', on_delete=models.CASCADE)

    class Meta:
        unique_together = (("order", "fly_zone"),)


"""
UAS Ordered Search Grid Points
"""
class OrderedSearchGridPoint(models.Model):
    # self-determined primary key
    latitude = models.FloatField()
    longitude = models.FloatField()
    order = models.IntegerField(db_index=True)
    search_grid = models.ForeignKey('SearchGrid', on_delete=models.CASCADE)

    class Meta:
        unique_together = (("order", "search_grid"),)
