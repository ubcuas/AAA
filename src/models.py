from django.db import models

class OrderedRouteWayPoint(models.Model):
    mission = models.ForeignKey('interop.UasMission', on_delete=models.CASCADE)
    altitude_msl = models.FloatField(null= True,
                                     default= 200.0) # [LL] TBD @Luc @Wesley
    latitude = models.FloatField()
    longitude = models.FloatField()
    order = models.IntegerField()

    delay = models.IntegerField(null=False, default=0)

    is_generated = models.BooleanField()

    wp_type_choices = ((x,x) for x in ('none','auto_flight', 'airdrop', 'search_grid', 'off_axis'))
    wp_type = models.CharField(default="none", max_length=128, choices=wp_type_choices)

    class Meta:
        unique_together = (("mission", "order"),)
