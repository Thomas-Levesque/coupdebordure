from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from races.models import Result
from .models import Bet, BetScore, compute_score_for_bet
from badges.services import update_unit_winner_badge, update_tour_badges
from races.models import Stage

def _recompute_for_unit(one_day_race, stage):
    bets = Bet.objects.filter(one_day_race=one_day_race, stage=stage)
    for bet in bets:
        score = compute_score_for_bet(bet)
        BetScore.objects.update_or_create(bet=bet, defaults={"score": score})

    # badges : vainqueur unité
    update_unit_winner_badge(one_day_race=one_day_race, stage=stage)

    # badges tour si étape
    if stage is not None:
        update_tour_badges(stage.tour)

@receiver(post_save, sender=Result)
def recompute_scores_on_result_save(sender, instance: Result, **kwargs):
    _recompute_for_unit(instance.one_day_race, instance.stage)

@receiver(post_delete, sender=Result)
def recompute_scores_on_result_delete(sender, instance: Result, **kwargs):
    _recompute_for_unit(instance.one_day_race, instance.stage)