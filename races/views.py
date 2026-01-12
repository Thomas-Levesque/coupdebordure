from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.translation import get_language

from .models import OneDayRace, Tour, Stage, Entry, Result
from bets.models import Bet, BetScore


def _lang2():
    return (get_language() or "fr")[:2].lower()


@login_required
def races_list_view(request):
    one_days = (
        OneDayRace.objects.select_related("season")
        .prefetch_related("translations")
        .all()
        .order_by("start_datetime")
    )
    tours = (
        Tour.objects.select_related("season")
        .prefetch_related("stages")
        .all()
        .order_by("start_datetime")
    )
    return render(request, "races/races_list.html", {"one_days": one_days, "tours": tours})


@login_required
def one_day_detail_view(request, race_id):
    lang = _lang2()

    race = get_object_or_404(
        OneDayRace.objects.prefetch_related("translations"),
        id=race_id
    )

    tr = next((t for t in race.translations.all() if t.language == lang), None)
    profile_text_display = (tr.profile_text if tr and tr.profile_text else race.profile_text)

    entries = Entry.objects.filter(one_day_race=race).select_related("rider").order_by("-odds", "rider__last_name")
    results = Result.objects.filter(one_day_race=race).select_related("rider").order_by("position")
    is_locked = timezone.now() >= race.start_datetime

    bet = Bet.objects.filter(user=request.user, one_day_race=race).select_related(
        "pick1","pick2","pick3","pick4","pick5"
    ).first()
    bet_score = BetScore.objects.filter(bet=bet).first() if bet else None

    return render(request, "races/unit_detail.html", {
        "unit_type": "one_day",
        "unit": race,
        "tour": None,
        "entries": entries,
        "results": results,
        "is_locked": is_locked,
        "start_datetime": race.start_datetime,
        "bet": bet,
        "bet_score": bet_score,
        "profile_text_display": profile_text_display,
    })


@login_required
def stage_detail_view(request, stage_id):
    lang = _lang2()

    stage = get_object_or_404(
        Stage.objects.select_related("tour").prefetch_related("translations"),
        id=stage_id
    )

    tr = next((t for t in stage.translations.all() if t.language == lang), None)
    profile_text_display = (tr.profile_text if tr and tr.profile_text else stage.profile_text)

    entries = Entry.objects.filter(stage=stage).select_related("rider").order_by("-odds", "rider__last_name")
    results = Result.objects.filter(stage=stage).select_related("rider").order_by("position")
    is_locked = timezone.now() >= stage.start_datetime

    bet = Bet.objects.filter(user=request.user, stage=stage).select_related(
        "pick1","pick2","pick3","pick4","pick5"
    ).first()
    bet_score = BetScore.objects.filter(bet=bet).first() if bet else None

    return render(request, "races/unit_detail.html", {
        "unit_type": "stage",
        "unit": stage,
        "tour": stage.tour,
        "entries": entries,
        "results": results,
        "is_locked": is_locked,
        "start_datetime": stage.start_datetime,
        "bet": bet,
        "bet_score": bet_score,
        "profile_text_display": profile_text_display,
    })