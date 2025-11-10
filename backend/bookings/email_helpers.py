"""
Email helper functions for Meister Barbershop
"""
from django.urls import reverse
from django.conf import settings

def build_review_url():
    """
    Returns the Google Maps review URL for Meister Barbershop.
    This is the direct link for customers to leave a Google review.
    """
    # Google Place ID for Meister Barbershop Erlangen
    place_id = "ChIJZ9Y2QhRQoUcRHm_f9XEbqzI"
    return f"https://search.google.com/local/writereview?placeid={place_id}"

def unsubscribe_followup_url(token, email=''):
    """
    Builds the absolute URL for unsubscribing from follow-up emails.
    
    Args:
        token: The unique unsubscribe token from FollowUpRequest
        email: Optional email address for verification
        
    Returns:
        Full HTTPS URL to the unsubscribe page with token as query parameter
    """
    path = reverse('unsubscribe_followup')
    domain = getattr(settings, 'SITE_DOMAIN', 'www.meisterbarbershop.de')
    base_url = f"https://{domain}{path}"
    
    # Add token and email as query parameters
    if email:
        return f"{base_url}?token={token}&email={email}"
    return f"{base_url}?token={token}"

def get_appointment_ics_attachment(appointment):
    """
    Generate ICS calendar file for appointment confirmation emails.
    
    Args:
        appointment: Appointment model instance
        
    Returns:
        Tuple of (filename, ics_content, mimetype)
    """
    try:
        from icalendar import Calendar, Event
        from datetime import datetime
        import pytz
        
        cal = Calendar()
        cal.add('prodid', '-//Meister Barbershop//meisterbarbershop.de//')
        cal.add('version', '2.0')
        
        event = Event()
        event.add('summary', f'Meister Barbershop - {appointment.service_type}')
        event.add('dtstart', appointment.start_at)
        event.add('dtend', appointment.end_at)
        event.add('location', 'Meister Barbershop, Luitpoldstraße 9, 91052 Erlangen')
        event.add('description', f'Termin mit {appointment.barber.get_full_name()}')
        
        cal.add_component(event)
        
        ics_content = cal.to_ical()
        filename = f'termin_{appointment.start_at.strftime("%Y%m%d")}.ics'
        
        return (filename, ics_content, 'text/calendar')
    except Exception as e:
        print(f"Error generating ICS: {e}")
        return None
