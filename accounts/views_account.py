from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from leagues.models import League
from badges.models import UserBadge

from .forms_account import ProfileForm
from .forms import NotificationPreferenceForm
from accounts.models import NotificationPreference

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.templatetags.static import static

from leagues.models import League
from badges.models import UserBadge
from accounts.models import NotificationPreference
from .forms_account import ProfileForm
from .forms import NotificationPreferenceForm

def _country_iso2(country_value) -> str:
    if not country_value:
        return ""
    code = getattr(country_value, "code", None)
    if code:
        return str(code).strip().lower()
    if isinstance(country_value, str):
        return country_value.strip().lower()
    return ""


@login_required
def account_view(request):
    profile = request.user.profile
    prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "notifications":
            notif_form = NotificationPreferenceForm(request.POST, instance=prefs)
            profile_form = ProfileForm(instance=profile, user=request.user)

            if notif_form.is_valid():
                notif_form.save()
                messages.success(request, "Préférences de notification mises à jour 🔔")
                return redirect("account")
            else:
                messages.error(request, "⚠️ Erreur : préférences de notifications non enregistrées.")

        elif form_type == "profile":
            profile_form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
            notif_form = NotificationPreferenceForm(instance=prefs)

            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profil mis à jour ✅")
                return redirect("account")
            else:
                messages.error(request, "⚠️ Erreur : profil non enregistré.")

        else:
            profile_form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
            notif_form = NotificationPreferenceForm(instance=prefs)

            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profil mis à jour ✅")
                return redirect("account")
            else:
                messages.error(request, "⚠️ Erreur : profil non enregistré.")
    else:
        profile_form = ProfileForm(instance=profile, user=request.user)
        notif_form = NotificationPreferenceForm(instance=prefs)

    my_leagues = (
        League.objects
        .filter(memberships__user=request.user)
        .distinct()
        .order_by("name")
    )

    my_badges = (
        UserBadge.objects
        .filter(user=request.user)
        .select_related("badge")
        .order_by("-awarded_at")
    )

    # ✅ Option A : drapeau safe (si tu veux l'utiliser dans le template)
    country_code = _country_iso2(profile.country)
    me_flag_url = static(f"flags/{country_code}.svg") if country_code else static("flags/_unknown.svg")

    return render(request, "accounts/account.html", {
        "form": profile_form,
        "notif_form": notif_form,
        "my_leagues": my_leagues,
        "my_badges": my_badges,
        "me_flag_url": me_flag_url,  # (optionnel)
    })