# ads/context_processors.py
from django.db.models import Q
from django.utils import timezone
from .models import AdPlacement


def ads_context(request):
    now = timezone.now()

    qs = (
        AdPlacement.objects
        .filter(is_active=True)
        .filter(Q(start_at__isnull=True) | Q(start_at__lte=now))
        .filter(Q(end_at__isnull=True) | Q(end_at__gte=now))
        .order_by("slot", "priority", "-created_at")
    )

    ads = {"top": None, "sidebar": None, "bottom": None}
    for ad in qs:
        if ads.get(ad.slot) is None:
            ads[ad.slot] = ad

    return {"ads": ads}