from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from bets.models import Bet, BetScore
from races.models import OneDayRace, Stage, Result, Entry


@login_required
def my_stats_view(request):
    user = request.user

    # --- Bets validés uniquement ---
    bets = Bet.objects.filter(user=user).exclude(submitted_at__isnull=True)

    played_total = bets.count()

    # --- Unités disponibles (simple) ---
    total_units = OneDayRace.objects.count() + Stage.objects.count()
    participation_rate = (played_total / total_units * 100) if total_units else 0

    # --- Scores ---
    scores_qs = BetScore.objects.filter(bet__user=user).select_related("bet")
    score_total = sum(float(s.score) for s in scores_qs)
    score_avg = (score_total / scores_qs.count()) if scores_qs.exists() else 0

    # --- Réussite sur top3 (via Result) ---
    # On prend top3 pour chaque unité et on compare aux picks
    win_exact = 0
    win_in_top5 = 0
    pick1_in_top3 = 0
    any_pick_in_top3 = 0
    units_with_results = 0

    for b in bets.select_related("one_day_race", "stage"):
        results = Result.objects.filter(one_day_race=b.one_day_race, stage=b.stage).order_by("position")[:3]
        if results.count() < 3:
            continue

        units_with_results += 1
        top3_ids = [r.rider_id for r in results]
        winner_id = results[0].rider_id

        picks = [b.pick1_id, b.pick2_id, b.pick3_id, b.pick4_id, b.pick5_id]
        picks = [pid for pid in picks if pid]

        if b.pick1_id and b.pick1_id in top3_ids:
            pick1_in_top3 += 1

        if any(pid in top3_ids for pid in picks):
            any_pick_in_top3 += 1

        if b.pick1_id == winner_id:
            win_exact += 1

        if winner_id in picks:
            win_in_top5 += 1

    # Taux (sur unités avec résultats)
    def rate(x):
        return (x / units_with_results * 100) if units_with_results else 0

    # --- Favori gagnant (par odds max) ---
    # Favori = rider avec odds max pour l'unité
    fav_wins = 0
    fav_total = 0
    user_had_fav = 0

    # On regarde uniquement les unités où il y a un gagnant
    # one-day
    for race in OneDayRace.objects.all():
        winner = Result.objects.filter(one_day_race=race, stage__isnull=True, position=1).first()
        if not winner:
            continue

        fav_entry = Entry.objects.filter(one_day_race=race, stage__isnull=True).order_by("-odds").first()
        if not fav_entry:
            continue

        fav_total += 1
        if winner.rider_id == fav_entry.rider_id:
            fav_wins += 1

        b = Bet.objects.filter(user=user, one_day_race=race).exclude(submitted_at__isnull=True).first()
        if b:
            picks = {b.pick1_id, b.pick2_id, b.pick3_id, b.pick4_id, b.pick5_id}
            if fav_entry.rider_id in picks:
                user_had_fav += 1

    # stages
    for stage in Stage.objects.all():
        winner = Result.objects.filter(stage=stage, one_day_race__isnull=True, position=1).first()
        if not winner:
            continue

        fav_entry = Entry.objects.filter(stage=stage, one_day_race__isnull=True).order_by("-odds").first()
        if not fav_entry:
            continue

        fav_total += 1
        if winner.rider_id == fav_entry.rider_id:
            fav_wins += 1

        b = Bet.objects.filter(user=user, stage=stage).exclude(submitted_at__isnull=True).first()
        if b:
            picks = {b.pick1_id, b.pick2_id, b.pick3_id, b.pick4_id, b.pick5_id}
            if fav_entry.rider_id in picks:
                user_had_fav += 1

    fav_win_rate = (fav_wins / fav_total * 100) if fav_total else 0

    context = {
        "played_total": played_total,
        "total_units": total_units,
        "participation_rate": participation_rate,

        "score_total": score_total,
        "score_avg": score_avg,

        "units_with_results": units_with_results,
        "win_exact": win_exact,
        "win_in_top5": win_in_top5,
        "pick1_in_top3": pick1_in_top3,
        "any_pick_in_top3": any_pick_in_top3,

        "rate_win_exact": rate(win_exact),
        "rate_win_in_top5": rate(win_in_top5),
        "rate_pick1_in_top3": rate(pick1_in_top3),
        "rate_any_pick_in_top3": rate(any_pick_in_top3),

        "fav_total": fav_total,
        "fav_wins": fav_wins,
        "fav_win_rate": fav_win_rate,
        "user_had_fav": user_had_fav,
    }
    return render(request, "stats/my_stats.html", context)
