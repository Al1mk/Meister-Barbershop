"""
API views for Telegram bot to fetch appointment data
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Appointment

SALON_TIME_ZONE = ZoneInfo("Europe/Berlin")

def serialize_appointment(appt):
    """Serialize appointment for Telegram bot"""
    return {
        "id": appt.id,
        "customer": appt.customer.name if appt.customer else "N/A",
        "barber": appt.barber.name if appt.barber else "N/A",
        "time": timezone.localtime(appt.start_at, SALON_TIME_ZONE).strftime("%H:%M"),
        "service": appt.get_service_type_display() if appt.service_type else str(appt.duration_minutes) + "min",
        "notes": ""
    }

@api_view(['GET'])
def today_appointments(request):
    """Get today's appointments"""
    now = timezone.now().astimezone(SALON_TIME_ZONE)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    appointments = Appointment.objects.filter(
        start_at__gte=today_start,
        start_at__lte=today_end,
        status__in=['booked', 'completed']
    ).select_related('customer', 'barber').order_by('start_at')
    
    return Response([serialize_appointment(appt) for appt in appointments])

@api_view(['GET'])
def tomorrow_appointments(request):
    """Get tomorrow's appointments"""
    now = timezone.now().astimezone(SALON_TIME_ZONE)
    tomorrow = now + timedelta(days=1)
    tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    appointments = Appointment.objects.filter(
        start_at__gte=tomorrow_start,
        start_at__lte=tomorrow_end,
        status__in=['booked', 'completed']
    ).select_related('customer', 'barber').order_by('start_at')
    
    return Response([serialize_appointment(appt) for appt in appointments])

@api_view(['GET'])
def stats_today(request):
    """Get today's statistics by barber"""
    now = timezone.now().astimezone(SALON_TIME_ZONE)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    appointments = Appointment.objects.filter(
        start_at__gte=today_start,
        start_at__lte=today_end,
        status__in=['booked', 'completed']
    ).select_related('barber')
    
    by_barber = defaultdict(int)
    for appt in appointments:
        barber_name = appt.barber.name if appt.barber else "Unknown"
        by_barber[barber_name] += 1
    
    return Response({
        "total": len(appointments),
        "by_barber": dict(by_barber)
    })
