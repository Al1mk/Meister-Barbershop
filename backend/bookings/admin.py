from django.contrib import admin
from .models import Customer, Appointment, Notification

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id","name","email","phone","created_at")
    search_fields = ("name","email","phone")

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("id","barber","customer","start_at","end_at","service_type","duration_minutes","status","reminder_sent","review_requested")
    list_filter = ("status","barber","service_type","reminder_sent","review_requested")
    search_fields = ("customer__name","customer__phone","customer__email")
    readonly_fields = ("confirmation_sent_at","reminder_sent","review_requested","review_request_sent_at","created_at")

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id","appointment","type","channel","status","sent_at")
    list_filter = ("type","channel","status")
