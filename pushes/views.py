import json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import PushSubscription


@require_GET
@login_required
def vapid_public_key(request):
    return JsonResponse({"publicKey": settings.VAPID_PUBLIC_KEY})


@require_POST
@login_required
def subscribe(request):
    # Le fetch JS enverra du JSON
    data = json.loads(request.body.decode("utf-8"))
    sub = data.get("subscription")
    if not sub:
        return JsonResponse({"ok": False, "error": "missing subscription"}, status=400)

    endpoint = sub.get("endpoint")
    keys = sub.get("keys", {})
    p256dh = keys.get("p256dh")
    auth = keys.get("auth")

    if not endpoint or not p256dh or not auth:
        return JsonResponse({"ok": False, "error": "invalid subscription"}, status=400)

    PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={"user": request.user, "p256dh": p256dh, "auth": auth},
    )
    return JsonResponse({"ok": True})
