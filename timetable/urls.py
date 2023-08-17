from django.urls import path
from . import views

urlpatterns = [
    path('s3/', views.download_file),
    path('stations/', views.read_stations_list)
]