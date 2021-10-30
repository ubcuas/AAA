from django.contrib import admin

from interop.models import *

# Register your models here.
class GpsPosition_admin(admin.ModelAdmin):
    list_display = ('latitude', 'longitude')
admin.site.register(GpsPosition, GpsPosition_admin)

class UasTelemetry_admin(admin.ModelAdmin):
    list_display = ('team', 'gps', 'altitude_msl', 'uas_heading', 'created_at', 'uploaded')
admin.site.register(UasTelemetry, UasTelemetry_admin)

class Team_admin(admin.ModelAdmin):
    list_display = ('team_id', 'username', 'name', 'university')
admin.site.register(Team, Team_admin)

class UasMission_admin(admin.ModelAdmin):
    list_display = ('id', 'active')
admin.site.register(UasMission, UasMission_admin)

class OrderedWayPoint_admin(admin.ModelAdmin):
    list_display = ('mission', 'order', 'latitude', 'longitude', 'altitude_msl')
admin.site.register(OrderedWayPoint, OrderedWayPoint_admin)

class OrderedBoundaryPoint_admin(admin.ModelAdmin):
    list_display = ('fly_zone', 'order', 'latitude', 'longitude')
admin.site.register(OrderedBoundaryPoint, OrderedBoundaryPoint_admin)

class OrderedSearchGridPoint_admin(admin.ModelAdmin):
    list_display = ('search_grid', 'order', 'latitude', 'longitude')
admin.site.register(OrderedSearchGridPoint, OrderedSearchGridPoint_admin)

class FlyZone_admin(admin.ModelAdmin):
    list_display = ('id', 'altitude_msl_max', 'altitude_msl_min')
admin.site.register(FlyZone, FlyZone_admin)

class SearchGrid_admin(admin.ModelAdmin):
    list_display = ('id',)
admin.site.register(SearchGrid, SearchGrid_admin)

class ClientSession_admin(admin.ModelAdmin):
    list_display = ('session_id', 'active', 'url')
admin.site.register(ClientSession, ClientSession_admin)
