from django.core.management.base import BaseCommand
from barbers.models import Barber


BARBERS = [
    {"name": "Javad", "working_days": "0,1,2,3,4,5"},
    {"name": "Iman", "working_days": "0,1,2,3,4,5"},
    {"name": "Ali", "working_days": "0,1,2,3,4,5"},
    {"name": "Ehsan", "working_days": "0,1,2,3,4,5"},
    {"name": "Reza", "working_days": "4,5"},
]

class Command(BaseCommand):
    help = "Seed default barbers"

    def handle(self, *args, **kwargs):
        created = 0
        for info in BARBERS:
            defaults = {
                "is_active": True,
                "working_days": info.get("working_days", "0,1,2,3,4,5"),
            }
            barber, was_created = Barber.objects.get_or_create(name=info["name"], defaults=defaults)
            if not was_created:
                for field, value in defaults.items():
                    setattr(barber, field, value)
                barber.save(update_fields=list(defaults.keys()))
            created += 1 if was_created else 0
        self.stdout.write(self.style.SUCCESS(f"Done. Created: {created}."))
