from django.core.exceptions import DisallowedHost
from rest_framework import serializers
from .models import Barber


class BarberSerializer(serializers.ModelSerializer):
    working_days = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()

    class Meta:
        model = Barber
        fields = ["id","name","photo","is_active","working_days"]

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
