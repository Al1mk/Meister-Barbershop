from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf import settings
from django.views.generic import RedirectView
from django.http import JsonResponse

urlpatterns = [
    path("", RedirectView.as_view(url="/api/docs/", permanent=False)),
    path("health/", lambda request: JsonResponse({"status": "ok"})),
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/barbers/", include("barbers.urls")),
    path("api/appointments/", include("bookings.urls")),
    path("api/contact/", include("contact.urls")),
    path("api/reviews/", include("reviews.urls")),
]


if settings.DEBUG:
    from django.views.static import serve as static_serve

    def media_serve(request, path):
        response = static_serve(request, path, document_root=settings.MEDIA_ROOT)
        response["Cache-Control"] = "public, max-age=86400, immutable"
        return response

    media_path = settings.MEDIA_URL.strip("/") or "media"
    urlpatterns += [
        path(f"{media_path}/<path:path>", media_serve, name="media"),
    ]
