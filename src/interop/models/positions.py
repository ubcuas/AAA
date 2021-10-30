from datetime import datetime
from django.db import models
from src.utils.conversions import meter_to_feet


class GpsPosition(models.Model):
    """GPS position consisting of a latitude and longitude degree value.
    This can be used for fly zone, drop location which represents an area or point on map

    Attributes:
        latitude: Latitude in degrees.
        longitude: Longitude in degrees.
    """
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)

    def __str__(self):
        return "pk %d with lat: %f lon: %f" % (self.pk, self.latitude, self.longitude)


class Team(models.Model):
    """
    Aircraft Team Data.
    Obtained from competition server

    Attributes:
        team_id: telemetry identifier team id. Given by interop. Used to relate data
                 to the telemetry model.
        username: aircraft team username,
        name: aircraft team name,
        university: aicraft team university
    """
    team_id = models.IntegerField(default=None, unique=True)
    username = models.CharField(max_length=256, blank=True)
    name = models.CharField(max_length=256, blank=True)
    university = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return "team_id: %d username: %s name: %s university: %s" % (
            self.team_id, self.username, self.name, self.university)


class UasTelemetry(models.Model):
    """
    Stores aircraft telemetry all teams (ours included),
    pulled from the interop server or put in by ourselves.
    Presently conforms to the data taken of this format:
    https://github.com/auvsi-suas/interop#get-apiteams

    Related to the on the Team model, where actual names and usernames are stored.

    Note that certain

    Attributes:
        team: Identifies the team that this belongs to. Related to Team model.
        gps: GPS longitude and latitude stored in GpsPosition model.
        altitude_msl: Altitude in meters. (meters) -> (converted to feet when posted)
        uas_heading: Aircraft heading (true north) in degrees (0-360). (degrees)
        uploaded: Boolean field, tells us whether or not certain telemetry has been uploaded to the server.
                  Allows us to know whether to send some telemetry or not (this value is always True
                  for foreign telemetry; telemetry that we've already received.)
        timestamp: The received timestamp of the telemetry,
                   according to the interop senarver. (datetime)
        created_at: Time at which the field was entered in the database.
    """
    team = models.ForeignKey(to=Team, default=None, to_field='team_id', on_delete=models.CASCADE)
    gps = models.OneToOneField(GpsPosition, on_delete=models.CASCADE)
    altitude_msl = models.FloatField()
    uas_heading = models.FloatField()
    uploaded = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=datetime.now())
    created_at = models.DateTimeField(auto_now_add=True)

    # POSTed to interop server https://github.com/auvsi-suas/interop#post-apitelemetry
    def marshal(self):
        return {'latitude': self.gps.latitude,
                'longitude': self.gps.longitude,
                'altitude': meter_to_feet(self.altitude_msl),
                'heading': self.uas_heading}