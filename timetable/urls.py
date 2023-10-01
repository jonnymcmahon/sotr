from django.urls import path
from . import views

urlpatterns = [
    path('s3/', views.parse_schedule),
    path('stations/', views.read_stations_list),
    path('tocs/', views.read_tocs),
    path('routes/', views.find_routes)
]