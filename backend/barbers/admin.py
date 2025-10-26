from django.contrib import admin

from .models import Barber, TimeOff


@admin.register(Barber)
class BarberAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active", "working_days")
    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(TimeOff)
class TimeOffAdmin(admin.ModelAdmin):
    list_display = ("barber", "start_date", "end_date", "reason")
    list_filter = ("barber", "start_date")
    search_fields = ("barber__name", "reason")
