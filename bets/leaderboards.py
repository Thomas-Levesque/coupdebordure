# bets/leaderboards.py
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from races.models import Season, OneDayRace, Stage, Tour
from .models import BetScore
from badges.services import award_badge, user_id_to_user

from .leaderboards_utils import finalize_rows, enrich_rows_with_profile, build_compact_rows


@login_required
def global_leaderboard(request, season_year):
    season = get_object_or_404(Season, year=season_year)

    qs_one_day = (
        BetScore.objects.filter(bet__one_day_race__season=season)
        .values("bet__user_id", "bet__user__username")
        .annotate(total=Sum("score"))
    )

    qs_stage = (
        BetScore.objects.filter(bet__stage__tour__season=season)
        .values("bet__user_id", "bet__user__username")
        .annotate(total=Sum("score"))
    )

    totals = {}
    for row in list(qs_one_day) + list(qs_stage):
        key = (row["bet__user_id"], row["bet__user__username"])
        totals[key] = totals.get(key, 0) + float(row["total"] or 0)

    rows_full = [{"user_id": k[0], "username": k[1], "total": v} for k, v in totals.items()]
    rows_full.sort(key=lambda r: (-r["total"], r["username"]))

    finalize_rows(rows_full, request.user.id)
    enrich_rows_with_profile(rows_full)

    rows = build_compact_rows(rows_full, request_user_id=request.user.id, top_n=3, bottom_n=3, around_user=1)

    # ⚠️ Anti-spam : ne pas award ici sur chaque refresh (à déplacer dans une tâche/cron ou quand la saison se termine)
    return render(request, "bets/leaderboard_global.html", {
        "season": season,
        "rows_full": rows_full,   # podium top3
        "rows": rows,             # tableau compact
    })


@login_required
def unit_leaderboard_one_day(request, race_id):
    race = get_object_or_404(OneDayRace, id=race_id)

    qs = (
        BetScore.objects
        .filter(bet__one_day_race=race)
        .values("bet__user_id", "bet__user__username")
        .annotate(total=Sum("score"))
        .order_by("-total", "bet__user__username")
    )

    rows_full = [
        {"user_id": r["bet__user_id"], "username": r["bet__user__username"], "total": float(r["total"] or 0)}
        for r in qs
    ]

    finalize_rows(rows_full, request.user.id)
    enrich_rows_with_profile(rows_full)
    rows = build_compact_rows(rows_full, request_user_id=request.user.id, top_n=3, bottom_n=3, around_user=1)

    return render(request, "bets/leaderboard_unit_compact.html", {
        "title": f"Classement — {race.name}",
        "rows_full": rows_full,
        "rows": rows,
    })


@login_required
def unit_leaderboard_stage(request, stage_id):
    stage = get_object_or_404(Stage.objects.select_related("tour"), id=stage_id)

    qs = (
        BetScore.objects
        .filter(bet__stage=stage)
        .values("bet__user_id", "bet__user__username")
        .annotate(total=Sum("score"))
        .order_by("-total", "bet__user__username")
    )

    rows_full = [
        {"user_id": r["bet__user_id"], "username": r["bet__user__username"], "total": float(r["total"] or 0)}
        for r in qs
    ]

    finalize_rows(rows_full, request.user.id)
    enrich_rows_with_profile(rows_full)
    rows = build_compact_rows(rows_full, request_user_id=request.user.id, top_n=3, bottom_n=3, around_user=1)

    return render(request, "bets/leaderboard_unit_compact.html", {
        "title": f"Classement — {stage}",
        "rows_full": rows_full,
        "rows": rows,
    })


@login_required
def tour_leaderboard(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)

    qs = (
        BetScore.objects
        .filter(bet__stage__tour=tour)
        .values("bet__user_id", "bet__user__username")
        .annotate(total=Sum("score"))
        .order_by("-total", "bet__user__username")
    )

    rows_full = [
        {"user_id": r["bet__user_id"], "username": r["bet__user__username"], "total": float(r["total"] or 0)}
        for r in qs
    ]

    finalize_rows(rows_full, request.user.id)
    enrich_rows_with_profile(rows_full)
    rows = build_compact_rows(rows_full, request_user_id=request.user.id, top_n=3, bottom_n=3, around_user=1)

    return render(request, "bets/leaderboard_tour_compact.html", {
        "tour": tour,
        "rows_full": rows_full,
        "rows": rows,
    })


CATEGORY_RULES = {
    "sprinteur": ("Classement sprinteur", [Stage.StageType.FLAT]),
    "grimpeur": ("Classement grimpeur", [Stage.StageType.MOUNTAIN]),
    "baroudeur": ("Classement baroudeur", [Stage.StageType.HILLY]),
    "rouleur": ("Classement rouleur (CLM)", [Stage.StageType.TT]),
}


@login_required
def tour_special_leaderboard(request, tour_id, category):
    tour = get_object_or_404(Tour, id=tour_id)

    if category not in CATEGORY_RULES:
        raise Http404("Catégorie inconnue")

    title, stage_types = CATEGORY_RULES[category]

    qs = (
        BetScore.objects
        .filter(bet__stage__tour=tour, bet__stage__stage_type__in=stage_types)
        .values("bet__user_id", "bet__user__username")
        .annotate(total=Sum("score"))
        .order_by("-total", "bet__user__username")
    )

    rows_full = [
        {"user_id": r["bet__user_id"], "username": r["bet__user__username"], "total": float(r["total"] or 0)}
        for r in qs
    ]

    finalize_rows(rows_full, request.user.id)
    enrich_rows_with_profile(rows_full)
    rows = build_compact_rows(rows_full, request_user_id=request.user.id, top_n=3, bottom_n=3, around_user=1)

    # (Optionnel) award winner ici = risque de spam si refresh → à déplacer plus tard
    # if rows_full:
    #     award_badge(user_id_to_user(rows_full[0]["user_id"]), "SPECIALIST_...", {"tour": tour.id})

    return render(request, "bets/leaderboard_tour_special_compact.html", {
        "tour": tour,
        "title": title,
        "category": category,
        "rows_full": rows_full,
        "rows": rows,
        "stage_types": stage_types,
    })


@login_required
def leaderboards_hub(request):
    seasons = Season.objects.all().order_by("-year")
    one_days = OneDayRace.objects.select_related("season").all().order_by("-start_datetime")[:30]
    tours = Tour.objects.select_related("season").all().order_by("-start_datetime")[:30]

    return render(request, "bets/leaderboards_hub.html", {
        "seasons": seasons,
        "one_days": one_days,
        "tours": tours,
    })