from django.urls import path

from .admin_views import BarberTimeOffView, TimeOffConflictsView, TimeOffDetailView

urlpatterns = [
    path("barbers/<int:barber_id>/timeoff", BarberTimeOffView.as_view(), name="admin-barber-timeoff"),
    path("timeoff/<int:pk>", TimeOffDetailView.as_view(), name="admin-timeoff-detail"),
    path("timeoff/conflicts", TimeOffConflictsView.as_view(), name="admin-timeoff-conflicts"),
]
