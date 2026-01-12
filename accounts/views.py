#accounts/views.py

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .forms import SignupForm
from django.db import models
from django.db.models import Sum
from badges.models import UserBadge
from django.templatetags.static import static
from accounts.models import Profile
from django.templatetags.static import static
from accounts.models import Profile
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Sum
from django.shortcuts import render
from django.templatetags.static import static
from django.utils import timezone

from accounts.models import Profile
from badges.models import UserBadge
from races.models import OneDayRace, Stage, Result
from bets.models import Bet, BetScore

# ✅ helper "Option A" : CountryField -> code ISO2 str
def _country_iso2(country_value) -> str:
    """
    country_value peut être:
      - un objet django_countries.fields.Country (=> .code)
      - une string ("fr")
      - vide / None
    Retourne "fr" ou "".
    """
    if not country_value:
        return ""
    code = getattr(country_value, "code", None)  # django-countries
    if code:
        return str(code).strip().lower()
    if isinstance(country_value, str):
        return country_value.strip().lower()
    return ""

def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()  # ✅ crée user + profile, user inactive

            # --- Email de bienvenue ---
            send_mail(
                subject=_("Bienvenue sur Coup de Bordure !"),
                message=_(
                    "Bonjour %(username)s,\n\n"
                    "Bienvenue sur Coup de Bordure 🎉\n"
                    "Confirme ton email pour activer ton compte.\n\n"
                    "À bientôt !"
                ) % {"username": user.username},
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            # --- Email de confirmation ---
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = email_verification_token.make_token(user)
            verify_url = request.build_absolute_uri(
                reverse("verify_email", kwargs={"uidb64": uid, "token": token})
            )

            send_mail(
                subject=_("Confirme ton email — Coup de Bordure"),
                message=_(
                    "Bonjour %(username)s,\n\n"
                    "Clique sur ce lien pour confirmer ton email :\n"
                    f"{verify_url}\n\n"
                    "Si tu n’es pas à l’origine de cette inscription, ignore ce message."
                ) % {"username": user.username},
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            messages.success(request, _("Compte créé ✅ Confirme ton email (voir console) puis connecte-toi."))
            return redirect("login")
    else:
        form = SignupForm()

    return render(request, "accounts/signup.html", {"form": form})

from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render

from races.models import OneDayRace, Stage, Result
from bets.models import Bet, BetScore

def _badge_icon_url_for_profile(profile: Profile) -> str:
    # upload > fallback static/badges/<code>.svg > _unknown.svg
    b = getattr(profile, "featured_badge", None)
    if not b:
        return ""
    icon = getattr(b, "icon", None)
    if icon:
        try:
            return icon.url
        except Exception:
            pass
    code = (getattr(b, "code", "") or "").strip().lower()
    return static(f"badges/{code}.svg") if code else static("badges/_unknown.svg")

from django.templatetags.static import static

def _badge_icon_url_for_badge(badge) -> str:
    # upload > fallback static/badges/<code>.svg > _unknown.svg
    if not badge:
        return static("badges/_unknown.svg")

    icon = getattr(badge, "icon", None)
    if icon:
        try:
            return icon.url
        except Exception:
            pass

    code = (getattr(badge, "code", "") or "").strip().lower()
    return static(f"badges/{code}.svg") if code else static("badges/_unknown.svg")


@login_required
def dashboard_view(request):
    now = timezone.now()

    # --- Récupérer les unités ---
    one_days = OneDayRace.objects.select_related("season").all()
    stages = Stage.objects.select_related("tour", "tour__season").all()

    # --- Bets de l'utilisateur (pour statuts top5/score) ---
    user_bets_one_day = {
        b.one_day_race_id: b
        for b in Bet.objects.filter(user=request.user, one_day_race__isnull=False)
        .select_related("pick1", "pick2", "pick3", "pick4", "pick5")
    }
    user_bets_stage = {
        b.stage_id: b
        for b in Bet.objects.filter(user=request.user, stage__isnull=False)
        .select_related("pick1", "pick2", "pick3", "pick4", "pick5")
    }

    # Scores (optionnel)
    score_by_bet_id = {
        s.bet_id: s
        for s in BetScore.objects.filter(bet__user=request.user)
        .select_related("bet")
    }

    # Résultats : on considère "terminé" si >= 3 résultats saisis
    results_count_one_day = {}
    for r in (
        Result.objects.filter(one_day_race__isnull=False)
        .values("one_day_race_id")
        .annotate(c=models.Count("id"))
    ):
        results_count_one_day[r["one_day_race_id"]] = r["c"]

    results_count_stage = {}
    for r in (
        Result.objects.filter(stage__isnull=False)
        .values("stage_id")
        .annotate(c=models.Count("id"))
    ):
        results_count_stage[r["stage_id"]] = r["c"]

    # Petit helper pour construire une carte "unité"
    def make_unit(kind, obj, start_dt, url_detail, url_bet, url_lb, tour=None):
        if kind == "one_day":
            bet = user_bets_one_day.get(obj.id)
            results_ok = results_count_one_day.get(obj.id, 0) >= 3
        else:
            bet = user_bets_stage.get(obj.id)
            results_ok = results_count_stage.get(obj.id, 0) >= 3

        locked = now >= start_dt
        has_top5 = bool(bet and bet.pick1 and bet.pick2 and bet.pick3 and bet.pick4 and bet.pick5)
        score_obj = score_by_bet_id.get(bet.id) if bet else None

        if results_ok:
            status = "finished"
        elif locked:
            status = "locked"
        else:
            status = "upcoming"

        return {
            "kind": kind,
            "obj": obj,
            "tour": tour,
            "start_dt": start_dt,
            "locked": locked,
            "results_ok": results_ok,
            "has_top5": has_top5,
            "bet": bet,
            "score": score_obj.score if score_obj else None,
            "submitted_at": bet.submitted_at if bet else None,
            "status": status,
            "url_detail": url_detail,
            "url_bet": url_bet,
            "url_lb": url_lb,
        }

    units = []

    for r in one_days:
        units.append(make_unit(
            kind="one_day",
            obj=r,
            start_dt=r.start_datetime,
            url_detail=("one_day_detail", r.id),
            url_bet=("bet_one_day", r.id),
            url_lb=("lb_one_day", r.id),
        ))

    for s in stages:
        units.append(make_unit(
            kind="stage",
            obj=s,
            start_dt=s.start_datetime,
            url_detail=("stage_detail", s.id),
            url_bet=("bet_stage", s.id),
            url_lb=("lb_stage", s.id),
            tour=s.tour,
        ))

    units.sort(key=lambda u: u["start_dt"])

    upcoming = [u for u in units if u["status"] == "upcoming"][:3]
    locked = [u for u in units if u["status"] == "locked"][:3]
    finished = [u for u in units if u["status"] == "finished"][:3]

    total_score = (
        BetScore.objects.filter(bet__user=request.user)
        .aggregate(total=Sum("score"))["total"]
        or 0
    )

    badges_recent = list(
        UserBadge.objects.filter(user=request.user)
        .select_related("badge")
        .order_by("-awarded_at")[:5]
    )
    for ub in badges_recent:
        ub.badge_icon_url = _badge_icon_url_for_badge(ub.badge)

    me_profile, _ = Profile.objects.select_related("featured_badge").get_or_create(user=request.user)

    me_avatar_url = me_profile.avatar_url

    # ✅ FIX django-countries : on prend le code ISO2
    country_code = _country_iso2(me_profile.country)
    me_flag_url = static(f"flags/{country_code}.svg") if country_code else static("flags/_unknown.svg")

    me_badge_icon_url = _badge_icon_url_for_profile(me_profile)

    return render(request, "accounts/dashboard.html", {
        "now": now,
        "upcoming": upcoming,
        "locked": locked,
        "finished": finished,
        "total_score": total_score,
        "badges_recent": badges_recent,
        "me_avatar_url": me_avatar_url,
        "me_flag_url": me_flag_url,
        "me_badge_icon_url": me_badge_icon_url,
    })

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from .tokens import email_verification_token

User = get_user_model()

def verify_email_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user and email_verification_token.check_token(user, token):
        user.is_active = True
        user.save(update_fields=["is_active"])
        messages.success(request, "Email confirmé ✅ Tu peux te connecter.")
        return redirect("login")

    messages.error(request, "Lien invalide ou expiré.")
    return redirect("home")


from .forms import NotificationPreferenceForm



from django.conf import settings
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.utils.translation import activate
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.i18n import set_language

from accounts.models import Profile


@require_POST
def set_language_pro(request):
    """
    1) Applique la langue via Django (cookie/session) en réutilisant set_language
    2) Persiste la préférence dans Profile.language si user authentifié
    3) Redirige vers `next`
    """
    lang = (request.POST.get("language") or "").strip()

    # sécurité: n'accepte que les langues déclarées dans settings.LANGUAGES
    allowed = {code for code, _ in getattr(settings, "LANGUAGES", [])}
    if lang not in allowed:
        lang = settings.LANGUAGE_CODE

    # Sauvegarde DB (si connecté)
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.language = lang
        profile.save(update_fields=["language"])

    # Applique côté Django (cookie / session)
    request.POST = request.POST.copy()
    request.POST["language"] = lang
    response = set_language(request)

    # Force activation pour la requête en cours (utile si tu rediriges juste après)
    activate(lang)

    # Redirection safe
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = "/"

    response["Location"] = next_url
    response.status_code = 302
    return response