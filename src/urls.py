from django.urls import path
from src import views
from django.conf.urls import re_path

urlpatterns = [
    re_path(r'^api/route/(?P<mission_id>[0-9]+)/$', views.route, name='aaa.api.route'),
    re_path(r'^api/reroute/(?P<mission_id>[0-9]+)/$', views.reroute, name='aaa.api.reroute'),
    re_path(r'^api/missions/$', views.missions, name='aaa.api.missions'),
    re_path(r'^file/route/(?P<mission_id>[0-9]+)/$', views.route_file, name='aaa.file.route'),
    re_path(r'^file/obs/(?P<mission_id>[0-9]+)/$', views.obs_file, name='aaa.file.obs'),
    re_path(r'^api/upload_to_acom/(?P<mission_id>[0-9]+)/$', views.upload_to_acom, name='aaa.api.upload_to_acom'),
]
