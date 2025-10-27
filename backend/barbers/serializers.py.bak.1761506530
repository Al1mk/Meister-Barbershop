from django.core.exceptions import DisallowedHost
from rest_framework import serializers

from .models import Barber, TimeOff


class BarberSerializer(serializers.ModelSerializer):
    working_days = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()

    class Meta:
        model = Barber
        fields = ["id", "name", "photo", "is_active", "working_days"]

    def get_working_days(self, obj):
        return sorted(obj.working_days_set())

    def get_photo(self, obj):
        if not obj.photo:
            return None
        request = self.context.get("request") if hasattr(self, "context") else None
        url = obj.photo.url
        if request:
            try:
                return request.build_absolute_uri(url)
            except DisallowedHost:
                pass
        return url


class TimeOffSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = TimeOff
        fields = ["id", "barber", "start_date", "end_date", "reason", "created_by", "created_at"]
        read_only_fields = ["id", "barber", "created_by", "created_at"]

    def get_created_by(self, obj):
        user = getattr(obj, "created_by", None)
        return user.get_username() if user else None


class TimeOffCreateSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    reason = serializers.CharField(max_length=120, allow_blank=True, required=False)
    force = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "end_date must be on or after start_date."})
        return attrs
