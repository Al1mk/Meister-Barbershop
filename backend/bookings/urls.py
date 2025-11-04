from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet
from . import api_views

router = DefaultRouter()
router.register(r"", AppointmentViewSet, basename="appointment")

urlpatterns = [
    path("today/", api_views.today_appointments, name="today"),
    path("tomorrow/", api_views.tomorrow_appointments, name="tomorrow"),
    path("stats/", api_views.stats_today, name="stats"),
    path("", include(router.urls)),
]
