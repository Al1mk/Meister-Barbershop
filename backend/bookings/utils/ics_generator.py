"""
ICS calendar file generator for appointment confirmations.
Generates RFC 5545 compliant iCalendar files with Europe/Berlin timezone.
"""
from datetime import datetime
from icalendar import Calendar, Event, vCalAddress, vText
from django.conf import settings
import pytz


def generate_appointment_ics(appointment) -> bytes:
    """
    Generate ICS calendar attachment for an appointment.

    Args:
        appointment: Appointment model instance

    Returns:
        bytes: ICS file content
    """
    cal = Calendar()
    cal.add('prodid', '-//Meister Barbershop//Appointment Booking//DE')
    cal.add('version', '2.0')
    cal.add('method', 'REQUEST')
    cal.add('calscale', 'GREGORIAN')

    event = Event()

    # Use Europe/Berlin timezone
    berlin_tz = pytz.timezone('Europe/Berlin')

    # Event times
    event.add('dtstart', appointment.start_at.astimezone(berlin_tz))
    event.add('dtend', appointment.end_at.astimezone(berlin_tz))
    event.add('dtstamp', datetime.now(berlin_tz))

    # Event details
    event.add('uid', f'appointment-{appointment.id}@meisterbarbershop.de')
    event.add('summary', f'Termin bei Meister Barbershop - {appointment.service_type}')

    # Description (bilingual)
    description = (
        f"Ihr Termin bei Meister Barbershop\n"
        f"Your appointment at Meister Barbershop\n\n"
        f"Service: {appointment.get_service_type_display()}\n"
        f"Barber: {appointment.barber.name}\n"
        f"Dauer / Duration: {appointment.duration_minutes} min\n\n"
        f"Adresse / Address:\n"
        f"Meister Barbershop\n"
        f"Hauptstraße 12\n"
        f"91054 Erlangen\n\n"
        f"Telefon / Phone: +49 9131 123456\n"
        f"Web: {settings.SITE_URL}"
    )
    event.add('description', description)

    # Location
    event.add('location', vText('Meister Barbershop, Hauptstraße 12, 91054 Erlangen, Deutschland'))

    # Organizer
    organizer = vCalAddress(f'mailto:{settings.DEFAULT_FROM_EMAIL}')
    organizer.params['cn'] = vText('Meister Barbershop')
    event['organizer'] = organizer

    # Attendee (customer)
    if appointment.customer and appointment.customer.email:
        attendee = vCalAddress(f'mailto:{appointment.customer.email}')
        attendee.params['cn'] = vText(appointment.customer.name)
        attendee.params['ROLE'] = vText('REQ-PARTICIPANT')
        attendee.params['PARTSTAT'] = vText('ACCEPTED')
        attendee.params['RSVP'] = vText('FALSE')
        event.add('attendee', attendee, encode=0)

    # Status and priority
    event.add('status', 'CONFIRMED')
    event.add('priority', 5)

    # Reminder: 1 hour before
    from icalendar import Alarm
    alarm = Alarm()
    alarm.add('action', 'DISPLAY')
    alarm.add('description', 'Erinnerung: Termin bei Meister Barbershop in 1 Stunde')
    alarm.add('trigger', '-PT1H')  # 1 hour before
    event.add_component(alarm)

    cal.add_component(event)

    return cal.to_ical()


def get_ics_filename(appointment) -> str:
    """Generate appropriate filename for ICS attachment."""
    date_str = appointment.start_at.strftime('%Y%m%d')
    return f'meister-barbershop-termin-{date_str}.ics'
