from rest_framework import generics
from .models import ContactMessage
from .serializers import ContactSerializer

class ContactCreateView(generics.CreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactSerializer