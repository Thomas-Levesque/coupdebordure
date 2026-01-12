from django.conf import settings
from django.db import models
from django.utils import timezone
from races.models import OneDayRace, Stage, Entry, Result

class Bet(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bets")

    one_day_race = models.ForeignKey(OneDayRace, on_delete=models.CASCADE, null=True, blank=True, related_name="bets")
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, null=True, blank=True, related_name="bets")

    pick1 = models.ForeignKey("races.Rider", on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    pick2 = models.ForeignKey("races.Rider", on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    pick3 = models.ForeignKey("races.Rider", on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    pick4 = models.ForeignKey("races.Rider", on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    pick5 = models.ForeignKey("races.Rider", on_delete=models.PROTECT, related_name="+", null=True, blank=True)

    submitted_at = models.DateTimeField(null=True, blank=True)  # validation horodatée
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "one_day_race"], name="uniq_bet_user_one_day"),
            models.UniqueConstraint(fields=["user", "stage"], name="uniq_bet_user_stage"),
        ]

    def clean(self):
        if (self.one_day_race is None) == (self.stage is None):
            raise ValueError("Bet: set exactly one of one_day_race OR stage.")

    def unit_start(self):
        if self.one_day_race:
            return self.one_day_race.start_datetime
        return self.stage.start_datetime

    def is_locked(self):
        return timezone.now() >= self.unit_start()

    def mark_submitted_now(self):
        self.submitted_at = timezone.now()

    def __str__(self):
        unit = self.one_day_race or self.stage
        return f"Bet({self.user} - {unit})"


class BetScore(models.Model):
    bet = models.OneToOneField(Bet, on_delete=models.CASCADE, related_name="score_obj")
    score = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    computed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Score({self.bet}={self.score})"


def _get_odds_for_unit_rider(one_day_race, stage, rider):
    entry = Entry.objects.filter(one_day_race=one_day_race, stage=stage, rider=rider).first()
    if not entry:
        return None
    return float(entry.odds)


def compute_score_for_bet(bet: Bet) -> float:
    """
    Calcule le score selon tes règles à partir du top3 officiel.
    """
    # Récupère top3 résultats
    results = Result.objects.filter(one_day_race=bet.one_day_race, stage=bet.stage).order_by("position")[:3]
    if results.count() < 3:
        return 0.0

    top3 = [r.rider_id for r in results]   # ids
    pos_by_rider = {results[i].rider_id: i + 1 for i in range(len(results))}

    picks = [bet.pick1, bet.pick2, bet.pick3, bet.pick4, bet.pick5]
    base_exact = [10, 7, 5, 3, 2]
    base_in_top3 = [4, 3, 2, 1, 1]

    total = 0.0
    for idx, rider in enumerate(picks):
        odds = _get_odds_for_unit_rider(bet.one_day_race, bet.stage, rider)
        if not odds or odds <= 0:
            continue
        inv_odds = 1.0 / odds

        expected_pos = idx + 1
        actual_pos = pos_by_rider.get(rider.id)  # 1..3 or None

        if actual_pos is None:
            continue

        if actual_pos == expected_pos and expected_pos <= 3:
            total += base_exact[idx] * inv_odds
        elif actual_pos <= 3:
            # dans top3 mais mauvaise place
            total += base_in_top3[idx] * inv_odds

    return total