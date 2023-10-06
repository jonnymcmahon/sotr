from django.urls import path
from . import views
from stompclient import views as views2

urlpatterns = [
    path('s3/', views.parse_schedule),
    path('stations/', views.read_stations_list),
    path('tocs/', views.read_tocs),
    path('routes/', views.find_route),
    path('stomp/', views2.handle),
    path('debug/', views.test_func)
]