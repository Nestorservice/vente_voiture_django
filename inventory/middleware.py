from django.utils import timezone
from datetime import timedelta
from .models import SiteVisit


class SiteVisitMiddleware:
    """Log each page visit — throttled to 1 per IP per 5 minutes for performance."""

    EXCLUDED_PATHS = ["/static/", "/media/", "/favicon.ico", "/admin/"]

    def __init__(self, get_response):
        self.get_response = get_response
        self._recent_ips = {}

    def __call__(self, request):
        response = self.get_response(request)

        path = request.path
        if any(path.startswith(p) for p in self.EXCLUDED_PATHS):
            return response

        if response.status_code != 200:
            return response

        # Skip AJAX requests
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return response

        try:
            x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
            ip = (
                x_forwarded.split(",")[0].strip()
                if x_forwarded
                else request.META.get("REMOTE_ADDR")
            )

            now = timezone.now()
            cache_key = f"{ip}:{path}"
            last_visit = self._recent_ips.get(cache_key)

            # Throttle to 1 visit per IP+path every 5 minutes
            if last_visit and (now - last_visit) < timedelta(seconds=300):
                return response

            self._recent_ips[cache_key] = now

            # Cleanup old entries less frequently
            if len(self._recent_ips) > 300:
                cutoff = now - timedelta(seconds=600)
                self._recent_ips = {
                    k: v for k, v in self._recent_ips.items() if v > cutoff
                }

            SiteVisit.objects.create(
                user=request.user if request.user.is_authenticated else None,
                ip_address=ip,
                page=path[:500],
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            )
        except Exception:
            pass

        return response
