# leagues/leaderboards.py
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, render

from bets.models import BetScore
from bets.leaderboards_utils import finalize_rows, enrich_rows_with_profile, build_compact_rows
from races.models import Season
from .models import League, LeagueMember


@login_required
def league_leaderboard_global(request, league_id, season_year):
    league = get_object_or_404(League, id=league_id)
    season = get_object_or_404(Season, year=season_year)

    member_ids = list(
        LeagueMember.objects.filter(league=league).values_list("user_id", flat=True)
    )

    # one-day
    rows_one_day = (
        BetScore.objects
        .filter(bet__user_id__in=member_ids, bet__one_day_race__season=season)
        .values("bet__user_id", "bet__user__username")
        .annotate(total=Sum("score"))
    )

    # stages
    rows_stage = (
        BetScore.objects
        .filter(bet__user_id__in=member_ids, bet__stage__tour__season=season)
        .values("bet__user_id", "bet__user__username")
        .annotate(total=Sum("score"))
    )

    totals = {}
    for row in list(rows_one_day) + list(rows_stage):
        key = (row["bet__user_id"], row["bet__user__username"])
        totals[key] = totals.get(key, 0) + float(row["total"] or 0)

    rows_full = [{"user_id": k[0], "username": k[1], "total": v} for k, v in totals.items()]
    rows_full.sort(key=lambda r: (-r["total"], r["username"]))

    finalize_rows(rows_full, request.user.id)
    enrich_rows_with_profile(rows_full)

    rows = build_compact_rows(rows_full, request_user_id=request.user.id, top_n=3, bottom_n=3, around_user=1)

    return render(request, "leagues/league_leaderboard_global.html", {
        "league": league,
        "season": season,
        "rows_full": rows_full,  # podium
        "rows": rows,            # compact + ellipses
    })