from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import serializers

from .models import Appointment, Customer

class CustomerInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["name","email","phone"]

class AppointmentCreateSerializer(serializers.ModelSerializer):
    customer = CustomerInlineSerializer()
    service_type = serializers.CharField(required=False, allow_blank=True)
    duration_minutes = serializers.IntegerField(required=False, min_value=1)

    class Meta:
        model = Appointment
        fields = ["barber", "start_at", "service_type", "duration_minutes", "customer"]

    def validate(self, attrs):
        c = attrs.get("customer") or {}
        for field in ("name", "email", "phone"):
            if not c.get(field):
                raise serializers.ValidationError(f"فیلد {field} الزامی است.")

        start_at = attrs.get("start_at")
        if start_at is None:
            raise serializers.ValidationError("start_at الزامی است.")

        if timezone.is_naive(start_at):
            start_local = timezone.make_aware(start_at, timezone.get_current_timezone())
        else:
            start_local = timezone.localtime(start_at)

        if start_local <= timezone.now():
            raise serializers.ValidationError("زمان گذشته قابل رزرو نیست.")

        normalized_type, duration = Appointment.normalize_service_meta(
            attrs.get("service_type"),
            attrs.get("duration_minutes"),
        )

        attrs["service_type"] = normalized_type or ""
        attrs["duration_minutes"] = duration
        return attrs

    def create(self, validated):
        cdata = validated.pop("customer")
        name = cdata["name"].strip()
        if not name:
            raise serializers.ValidationError("نام مشتری نمی‌تواند خالی باشد.")

        email = cdata["email"].lower().strip()
        phone = cdata["phone"].strip()

        customer, _ = Customer.objects.get_or_create(
            email=email,
            phone=phone,
            defaults={"name": name},
        )

        try:
            appt = Appointment.objects.create(customer=customer, **validated)
        except IntegrityError:
            raise serializers.ValidationError("این اسلات قبلاً رزرو شده است.")
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict or exc.messages)
        return appt

class AppointmentOutSerializer(serializers.ModelSerializer):
    customer = CustomerInlineSerializer()
    class Meta:
        model = Appointment
        fields = [
            "id",
            "barber",
            "start_at",
            "end_at",
            "service_type",
            "duration_minutes",
            "status",
            "customer",
            "confirmation_sent_at",
            "review_request_sent_at",
            "created_at",
        ]
