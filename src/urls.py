from django.urls import path
from avoidance import views
from django.conf.urls import re_path

urlpatterns = [
    re_path(r'^api/route/(?P<mission_id>[0-9]+)/$', views.route, name='avoidance.api.route'),
    re_path(r'^api/reroute/(?P<mission_id>[0-9]+)/$', views.reroute, name='avoidance.api.reroute'),
    re_path(r'^api/missions/$', views.missions, name='avoidance.api.missions'),
    re_path(r'^file/route/(?P<mission_id>[0-9]+)/$', views.route_file, name='avoidance.file.route'),
    re_path(r'^file/obs/(?P<mission_id>[0-9]+)/$', views.obs_file, name='avoidance.file.obs'),
    re_path(r'^api/upload_to_acom/(?P<mission_id>[0-9]+)/$', views.upload_to_acom, name='avoidance.api.upload_to_acom'),
]
