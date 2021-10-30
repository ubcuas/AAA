import json
from django.db import models
from interop.models import *
from src.utils.conversions import feet_to_meter

class UasMission(models.Model):
    # mission id - primary key
    id = models.IntegerField(primary_key=True)
    active = models.BooleanField()
    airdrop_pos = models.ForeignKey('GpsPosition', related_name="airdrop_pos", on_delete=models.CASCADE, null=True)
    off_axis_odlc_pos = models.ForeignKey('GpsPosition', related_name="off_axis_odlc_pos", on_delete=models.CASCADE, null=True)
    emergent_last_known_pos = models.ForeignKey('GpsPosition', related_name="emergent_last_known_pos", on_delete=models.CASCADE, null=True)

    flyzone = models.ForeignKey('FlyZone', on_delete=models.CASCADE, null=True)
    search_grid = models.ForeignKey('SearchGrid', on_delete=models.CASCADE, null=True)


    def get_waypoints_as_list(self):
        return OrderedWayPoint.objects.filter(mission=self.id).order_by('order')

    def get_obstacles_as_list(self):
        return Obstacle.objects.filter(mission=self.id)

    @classmethod
    def create(cls, interop_mission):
        # Create the mission model
        mission = cls(id = interop_mission['id'], active = True)

        # Add the air drop position to the model
        airdrop_pos = GpsPosition.objects.create(latitude = interop_mission['airDropPos']['latitude'],
                                                 longitude = interop_mission['airDropPos']['longitude'])
        airdrop_pos.save()
        mission.airdrop_pos = airdrop_pos

        # Add the off_axis_odlc position to the model
        off_axis_odlc_pos = GpsPosition.objects.create(latitude = interop_mission['offAxisOdlcPos']['latitude'],
                                                       longitude = interop_mission['offAxisOdlcPos']['longitude'])
        off_axis_odlc_pos.save()
        mission.off_axis_odlc_pos = off_axis_odlc_pos

        # Add the emergent_last_known position to the model
        emergent_last_known_pos = GpsPosition.objects.create(latitude = interop_mission['emergentLastKnownPos']['latitude'],
                                                            longitude = interop_mission['emergentLastKnownPos']['longitude'])
        emergent_last_known_pos.save()
        mission.emergent_last_known_pos = emergent_last_known_pos

        # Create flyzone
        # TODO: Handle multiple flyzones
        flyzone = FlyZone.create(interop_mission['flyZones'][0])
        flyzone.save()
        mission.flyzone = flyzone

        # Create search grid
        search_grid = SearchGrid.create(search_grid_points=interop_mission['searchGridPoints'])
        search_grid.save()
        mission.search_grid = search_grid

        # Save the mission!
        old_missions = UasMission.objects.filter(id=mission.id)
        for old_mission in old_missions:
            old_mission.delete()  # Need to call the single item delete to use the delete function override
        mission.save()

        # Add the mission waypoints
        order = 0
        for imwp in interop_mission['waypoints']:
            mwp = OrderedWayPoint.objects.create(mission = mission,
                                                 altitude_msl = feet_to_meter(imwp['altitude']),
                                                 latitude = imwp['latitude'],
                                                 longitude = imwp['longitude'],
                                                 order = order)
            mwp.save()
            order += 1

        # Add the obstacles
        for iobs in interop_mission['stationaryObstacles']:
            obs = Obstacle.objects.create(mission = mission,
                                          cylinder_height = feet_to_meter(iobs['height']),
                                          cylinder_radius = feet_to_meter(iobs['radius']),
                                          latitude = iobs['latitude'],
                                          longitude = iobs['longitude'])
            obs.save()
        return mission

    def delete(self, using=None):
        if self.airdrop_pos:
            self.airdrop_pos.delete()
        if self.off_axis_odlc_pos:
            self.off_axis_odlc_pos.delete()
        if self.emergent_last_known_pos:
            self.emergent_last_known_pos.delete()
        if self.flyzone:
            self.flyzone.delete()
        if self.search_grid:
            self.search_grid.delete()
        super().delete(using)

"""
UAS Flyzone class
"""
class FlyZone(models.Model):
    # self determined primary key
    altitude_msl_max = models.FloatField()
    altitude_msl_min = models.FloatField()

    @classmethod
    def create(cls, fly_zone):
        uasfly_zone = cls(altitude_msl_max = feet_to_meter(fly_zone['altitudeMax']),
                          altitude_msl_min = feet_to_meter(fly_zone['altitudeMin']))
        uasfly_zone.save()

        order = 0
        for bp in fly_zone['boundaryPoints']:
            boundry_pt = OrderedBoundaryPoint.objects.create(
                                           latitude= bp['latitude'],
                                           longitude= bp['longitude'],
                                           fly_zone= uasfly_zone,
                                           order= order)
            boundry_pt.save()
            order += 1

        return uasfly_zone

    def get_waypoints_as_list(self):
        return OrderedBoundaryPoint.objects.filter(fly_zone=self.id).order_by('order')

    def get_vertical_bounds(self):
        return (self.altitude_msl_min, self.altitude_msl_max)

"""
UAS Search Grid class
"""
class SearchGrid(models.Model):
    # self determined primary key

    @classmethod
    def create(cls, search_grid_points):
        search_grid = cls()
        search_grid.save()

        order = 0
        for sgp in search_grid_points:
            searchgrid_pt = OrderedSearchGridPoint.objects.create(
                                           latitude=sgp['latitude'],
                                           longitude=sgp['longitude'],
                                           search_grid=search_grid,
                                           order= order)
            searchgrid_pt.save()
            order += 1

        return search_grid

    def get_waypoints_as_list(self):
        return OrderedSearchGridPoint.objects.filter(search_grid=self.id).order_by('order')
