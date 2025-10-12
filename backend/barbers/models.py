from django.db import models

def barber_photo_path(instance, filename):
    return f"barbers/{instance.id}/{filename}"

class Barber(models.Model):
    name = models.CharField(max_length=50, unique=True)
    photo = models.ImageField(upload_to=barber_photo_path, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    working_days = models.CharField(
        max_length=20,
        default="0,1,2,3,4,5",
        help_text="Comma separated weekday numbers (0=Mon ... 6=Sun).",
    )

    def __str__(self):
        return self.name

    def working_days_set(self) -> set[int]:
        values = set()
        for part in self.working_days.split(","):
            part = part.strip()
            if part.isdigit():
                values.add(int(part))
        return values
