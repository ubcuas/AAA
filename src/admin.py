from django.contrib import admin

from src.models import OrderedRouteWayPoint

# Register your models here.
class OrderedRouteWayPoint_admin(admin.ModelAdmin):
    list_display = ('mission', 'order', 'latitude', 'longitude', 'altitude_msl', 'is_generated')
admin.site.register(OrderedRouteWayPoint, OrderedRouteWayPoint_admin)