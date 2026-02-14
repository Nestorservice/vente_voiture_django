from django.utils import timezone
from datetime import timedelta
from .models import SiteVisit


class SiteVisitMiddleware:
    """Log each page visit for activity tracking — throttled to 1 per IP per minute."""

    EXCLUDED_PATHS = ["/static/", "/media/", "/favicon.ico"]

    def __init__(self, get_response):
        self.get_response = get_response
        self._recent_ips = {}  # Simple in-memory throttle

    def __call__(self, request):
        response = self.get_response(request)

        # Skip static/media/ajax requests
        path = request.path
        if any(path.startswith(p) for p in self.EXCLUDED_PATHS):
            return response

        # Skip non-200 responses
        if response.status_code != 200:
            return response

        try:
            # Get client IP
            x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
            ip = (
                x_forwarded.split(",")[0].strip()
                if x_forwarded
                else request.META.get("REMOTE_ADDR")
            )

            # Throttle: skip if this IP was logged in the last 60 seconds
            now = timezone.now()
            cache_key = f"{ip}:{path}"
            last_visit = self._recent_ips.get(cache_key)
            if last_visit and (now - last_visit) < timedelta(seconds=60):
                return response

            self._recent_ips[cache_key] = now

            # Clean old entries every 100 requests to prevent memory growth
            if len(self._recent_ips) > 500:
                cutoff = now - timedelta(seconds=120)
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
            pass  # Never break the site for analytics

        return response
