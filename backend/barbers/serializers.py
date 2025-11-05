from rest_framework import serializers
from .models import Barber


class BarberSerializer(serializers.ModelSerializer):
    working_days = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()

    class Meta:
        model = Barber
        fields = ["id", "name", "photo", "is_active", "working_days"]

    def get_working_days(self, obj):
        return sorted(obj.working_days_set())

    def get_photo(self, obj):
        """Return photo URL - simple version without request.build_absolute_uri() to avoid hangs."""
        if not obj.photo:
            return None
        try:
            # Try to build absolute URI if request is available
            request = self.context.get("request")
            if request:
                # Use a simpler approach that wont hang
                from django.conf import settings
                base_url = f"{request.scheme}://{request.get_host()}"
                return f"{base_url}{obj.photo.url}"
        except Exception:
            pass
        # Fallback to relative URL
        return obj.photo.url
