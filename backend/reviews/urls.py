from django.urls import path

from .views import reviews_view

urlpatterns = [
    path("", reviews_view, name="reviews"),
    path("google", reviews_view, name="reviews-google"),
]
