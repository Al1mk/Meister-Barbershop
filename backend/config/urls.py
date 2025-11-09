from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import RedirectView
from django.views.static import serve as static_serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from bookings.unsubscribe_views import unsubscribe_followup
from bookings.webhook_views import mailgun_webhook, sendgrid_webhook
from bookings.metrics_views import email_metrics

urlpatterns = [
    path("", RedirectView.as_view(url="/api/docs/", permanent=False)),
    path("health/", lambda request: JsonResponse({"status": "ok"})),
    path("health/email-metrics/", email_metrics, name="email_metrics"),
    path("admin/", admin.site.urls),
    path("unsubscribe-followup/", unsubscribe_followup, name="unsubscribe_followup"),
    path("email-webhook/mailgun/", mailgun_webhook, name="mailgun_webhook"),
    path("email-webhook/sendgrid/", sendgrid_webhook, name="sendgrid_webhook"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/barbers/", include("barbers.urls")),
    path("api/admin/", include("barbers.admin_urls")),
    path("api/appointments/", include("bookings.urls")),
    path("api/contact/", include("contact.urls")),
    path("api/reviews/", include("reviews.urls")),
]


def media_serve(request, path):
    response = static_serve(request, path, document_root=settings.MEDIA_ROOT)
    response["Cache-Control"] = "public, max-age=86400, immutable"
    return response


media_path = settings.MEDIA_URL.strip("/") or "media"
urlpatterns += [
    path(f"{media_path}/<path:path>", media_serve, name="media"),
]
