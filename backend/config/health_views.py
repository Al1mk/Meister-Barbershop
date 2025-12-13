"""
Health check endpoints for production monitoring.

These endpoints verify core system functionality beyond simple HTTP response.
"""

from django.http import JsonResponse
from django.db import connection
from django.utils import timezone


def health_basic(request):
    """Basic health check - HTTP 200 only."""
    return JsonResponse({"status": "ok"})


def health_booking(request):
    """
    Deep health check for booking system.

    Verifies:
    1. Database connectivity
    2. Appointment model query
    3. Barber model query
    4. Relational query (appointment.select_related)

    Returns HTTP 200 + JSON if all checks pass.
    Returns HTTP 500 + error details if any check fails.
    """
    checks = {}
    errors = []

    try:
        # Check 1: Database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            checks["database"] = "ok"
    except Exception as e:
        checks["database"] = "error"
        errors.append(f"Database connectivity failed: {str(e)}")

    try:
        # Check 2: Appointment model query
        from bookings.models import Appointment
        appointment_count = Appointment.objects.count()
        checks["appointments"] = {
            "status": "ok",
            "count": appointment_count
        }
    except Exception as e:
        checks["appointments"] = "error"
        errors.append(f"Appointment query failed: {str(e)}")

    try:
        # Check 3: Barber model query
        from barbers.models import Barber
        barber_count = Barber.objects.filter(is_active=True).count()
        checks["barbers"] = {
            "status": "ok",
            "count": barber_count
        }
    except Exception as e:
        checks["barbers"] = "error"
        errors.append(f"Barber query failed: {str(e)}")

    try:
        # Check 4: Relational query (booking → barber)
        from bookings.models import Appointment
        latest_appointment = Appointment.objects.select_related("barber", "customer").first()
        if latest_appointment:
            # Verify we can access related objects without additional queries
            _ = latest_appointment.barber.name
            _ = latest_appointment.customer.name
        checks["relations"] = "ok"
    except Exception as e:
        checks["relations"] = "error"
        errors.append(f"Relational query failed: {str(e)}")

    # Determine overall status
    has_errors = len(errors) > 0
    status_code = 500 if has_errors else 200

    response_data = {
        "status": "error" if has_errors else "ok",
        "timestamp": timezone.now().isoformat(),
        "checks": checks,
    }

    if has_errors:
        response_data["errors"] = errors

    return JsonResponse(response_data, status=status_code)
