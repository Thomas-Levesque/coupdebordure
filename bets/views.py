from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from races.models import OneDayRace, Stage
from .forms import BetForm
from .models import Bet, compute_score_for_bet, BetScore

from badges import services as badge_services


@login_required
def bet_for_one_day_view(request, race_id):
    race = get_object_or_404(OneDayRace, id=race_id)

    if timezone.now() >= race.start_datetime:
        messages.error(request, "Pronostics verrouillés (course commencée).")
        return redirect("one_day_detail", race_id=race.id)

    bet, _ = Bet.objects.get_or_create(
        user=request.user,
        one_day_race=race,
        defaults={"pick1": None, "pick2": None, "pick3": None, "pick4": None, "pick5": None},
    )

    if request.method == "POST":
        form = BetForm(request.POST, instance=bet, one_day_race=race, stage=None)
        if form.is_valid():
            bet = form.save(commit=False)
            bet.mark_submitted_now()
            bet.save()

            # ✅ badge "premier prono"
            badge_services.award_first_bet(request.user)

            # ✅ badges saison (option 1 : au moins 1 étape jouée)
            try:
                badge_services.evaluate_user_badges_for_season(
                    request.user,
                    year=bet.unit_start().year
                )
            except Exception:
                # On n'empêche jamais l'enregistrement du prono si un badge plante
                pass

            # score 0 tant que pas de résultats, mais on peut initialiser
            score = compute_score_for_bet(bet)
            BetScore.objects.update_or_create(bet=bet, defaults={"score": score})

            messages.success(request, "Prono enregistré ✅")
            return redirect("one_day_detail", race_id=race.id)
    else:
        form = BetForm(instance=bet, one_day_race=race, stage=None)

    return render(request, "bets/bet_form.html", {"form": form, "unit": race, "unit_name": race.name})


@login_required
def bet_for_stage_view(request, stage_id):
    stage = get_object_or_404(Stage.objects.select_related("tour"), id=stage_id)

    if timezone.now() >= stage.start_datetime:
        messages.error(request, "Pronostics verrouillés (étape commencée).")
        return redirect("stage_detail", stage_id=stage.id)

    bet, _ = Bet.objects.get_or_create(
        user=request.user,
        stage=stage,
        defaults={"pick1": None, "pick2": None, "pick3": None, "pick4": None, "pick5": None},
    )

    if request.method == "POST":
        form = BetForm(request.POST, instance=bet, one_day_race=None, stage=stage)
        if form.is_valid():
            bet = form.save(commit=False)
            bet.mark_submitted_now()
            bet.save()

            badge_services.award_first_bet(request.user)

            try:
                badge_services.evaluate_user_badges_for_season(
                    request.user,
                    year=bet.unit_start().year
                )
            except Exception:
                pass

            score = compute_score_for_bet(bet)
            BetScore.objects.update_or_create(bet=bet, defaults={"score": score})

            messages.success(request, "Prono enregistré ✅")
            return redirect("stage_detail", stage_id=stage.id)
    else:
        form = BetForm(instance=bet, one_day_race=None, stage=stage)

    return render(request, "bets/bet_form.html", {"form": form, "unit": stage, "unit_name": str(stage)})