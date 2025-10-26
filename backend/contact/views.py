from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .serializers import ContactSerializer
import logging

logger = logging.getLogger(__name__)

class ContactCreateView(APIView):
    def post(self, request):
        serializer = ContactSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"ok": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        message = data.get('message', '').strip()
        
        # Validate required fields
        if not name or not message:
            return Response(
                {"ok": False, "error": "Name and message are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prepare email content
        email_subject = f"New contact form message - Meister Barbershop"
        email_body = f"""
New Contact Form Submission
============================

Name: {name}
Phone: {phone if phone else 'Not provided'}

Message:
{message}

---
Sent from Meister Barbershop website contact form
"""
        
        try:
            # Send email
            send_mail(
                subject=email_subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['meister.barbershop.erlangen@gmail.com'],
                fail_silently=False,
            )
            
            logger.info(f"Contact form email sent successfully from {name}")
            return Response({"ok": True}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to send contact form email: {str(e)}")
            return Response(
                {"ok": False, "error": "Failed to send message."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
