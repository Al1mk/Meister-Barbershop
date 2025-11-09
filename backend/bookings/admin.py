from django.contrib import admin
from .models import Customer, Appointment, Notification, FollowUpRequest

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

@admin.register(FollowUpRequest)
class FollowUpRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "appointment_id", "sent_at", "opt_out", "bounce_type", "complaint")
    list_filter = ("opt_out", "bounce_type", "complaint", "lang")
    search_fields = ("email", "phone")
    readonly_fields = ("sent_at", "opted_out_at", "opted_out_ip", "webhook_event_data")
    list_per_page = 50

    fieldsets = (
        ("Email Information", {
            "fields": ("email", "phone", "appointment", "lang")
        }),
        ("Status", {
            "fields": ("opt_out", "opted_out_at", "opted_out_ip", "sent_at")
        }),
        ("Bounce & Complaint Tracking", {
            "fields": ("bounce_type", "complaint", "webhook_event_data"),
            "classes": ("collapse",)
        }),
    )
