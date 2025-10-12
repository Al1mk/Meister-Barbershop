from django.db.models import Case, IntegerField, Value, When
from rest_framework import viewsets

from .models import Barber
from .serializers import BarberSerializer

# We want a custom display order instead of relying on creation order.
BARBER_ORDER = ["Ehsan", "Iman", "Javad", "Ali", "Reza"]
BARBER_PRIORITY = Case(
    *[
        When(name=name, then=Value(index))
        for index, name in enumerate(BARBER_ORDER)
    ],
    default=Value(len(BARBER_ORDER)),
    output_field=IntegerField(),
)


class BarberViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Barber.objects.filter(is_active=True)
        .annotate(order_priority=BARBER_PRIORITY)
        .order_by("order_priority", "id")
    )
    serializer_class = BarberSerializer
