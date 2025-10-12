from django.contrib import admin
from .models import Barber

@admin.register(Barber)
class BarberAdmin(admin.ModelAdmin):
    list_display = ("id","name","is_active","working_days")
    search_fields = ("name",)
    list_filter = ("is_active",)
