from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.api_health),
    path("forecast/", views.api_forecast),
    path("impact/", views.api_impact),
    path("graph/", views.api_graph),
    path("executive/", views.api_executive),
]
