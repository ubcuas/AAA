from django.urls import path
from interop import views
from django.conf.urls import url

urlpatterns = [
    url(r'api/interop/login$', views.login, name='interop.login'),
    url(r'api/interop/mission$', views.mission, name='interop.mission'),
    url(r'api/interop/status$', views.status, name='interop.status'),
    url(r'api/interop/telemetry$', views.telemetry, name='interop.telemetry'),
    url(r'api/interop/teamtelemetry$', views.teams, name='interop.teamtelemetry'),
    url(r'api/interop/telemstatus$', views.telem_status, name='interop.telem_status'),
    url(r'api/interop/teamtelemstatus$', views.team_telem_status, name='interop.team_telem_status')
]
