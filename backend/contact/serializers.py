from rest_framework import serializers
from .models import ContactMessage

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["id","name","email","phone","message","created_at"]
        read_only_fields = ["id","created_at"]

    def validate(self, attrs):
        name = (attrs.get("name") or "").strip()
        email = (attrs.get("email") or "").strip()
        phone = (attrs.get("phone") or "").strip()
        message = (attrs.get("message") or "").strip()

        if not name:
            raise serializers.ValidationError("نام الزامی است.")
        if not message:
            raise serializers.ValidationError("پیام نمی‌تواند خالی باشد.")
        if not email and not phone:
            raise serializers.ValidationError("حداقل یکی از فیلدهای ایمیل یا تلفن را پر کنید.")

        attrs["name"] = name
        attrs["email"] = email
        attrs["phone"] = phone
        attrs["message"] = message
        return attrs
