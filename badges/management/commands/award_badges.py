from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Max, Count

from badges.models import Badge, UserBadge
from bets.models import Bet, BetScore
from races.models import OneDayRace, Stage
from races.models import Result  # ton modèle Result vit dans races.models d'après ton code

BADGE_CODES = ["WINNER_UNIT", "PODIUM_UNIT", "TOP5_UNIT"]


def _get_badges():
    badges = {b.code: b for b in Badge.objects.filter(code__in=BADGE_CODES)}
    missing = [c for c in BADGE_CODES if c not in badges]
    if missing:
        raise CommandError(
            f"Badges manquants: {missing}. Lance d'abord: python manage.py seed_badges"
        )
    return badges


def _is_finished_one_day(one_day_id: int) -> bool:
    return Result.objects.filter(one_day_race_id=one_day_id).count() >= 3


def _is_finished_stage(stage_id: int) -> bool:
    return Result.objects.filter(stage_id=stage_id).count() >= 3


def _award_for_unit(kind: str, unit_id: int, dry_run: bool = False) -> dict:
    """
    kind: 'one_day' ou 'stage'
    unit_id: id de OneDayRace ou Stage
    """
    badges = _get_badges()

    if kind == "one_day":
        if not OneDayRace.objects.filter(id=unit_id).exists():
            raise CommandError(f"OneDayRace id={unit_id} introuvable.")
        if not _is_finished_one_day(unit_id):
            return {"skipped": 1, "reason": "not_finished"}

        qs = (BetScore.objects
              .filter(bet__one_day_race_id=unit_id)
              .select_related("bet", "bet__user")
              .order_by("-score"))

    elif kind == "stage":
        if not Stage.objects.filter(id=unit_id).exists():
            raise CommandError(f"Stage id={unit_id} introuvable.")
        if not _is_finished_stage(unit_id):
            return {"skipped": 1, "reason": "not_finished"}

        qs = (BetScore.objects
              .filter(bet__stage_id=unit_id)
              .select_related("bet", "bet__user")
              .order_by("-score"))
    else:
        raise CommandError("kind invalide. Utilise 'one_day' ou 'stage'.")

    scores = list(qs[:5])  # top 5
    if not scores:
        return {"skipped": 1, "reason": "no_scores"}

    winners = scores[:1]
    podium = scores[:3]
    top5 = scores[:5]

    created = 0

    def give(user, badge_code: str):
        nonlocal created
        if dry_run:
            return
        obj, was_created = UserBadge.objects.get_or_create(
            user=user,
            badge=badges[badge_code],
            defaults={"context": {"kind": kind, "unit_id": unit_id}},
        )
        created += int(was_created)

    for s in winners:
        give(s.bet.user, "WINNER_UNIT")
    for s in podium:
        give(s.bet.user, "PODIUM_UNIT")
    for s in top5:
        give(s.bet.user, "TOP5_UNIT")

    return {"created": created, "top_n": len(scores)}


class Command(BaseCommand):
    help = "Attribue les badges (winner/podium/top5) selon BetScore.score, par course/étape ou pour toutes les unités finies."

    def add_arguments(self, parser):
        parser.add_argument("--kind", choices=["one_day", "stage"], help="Type d'unité.")
        parser.add_argument("--id", type=int, help="ID de l'unité.")
        parser.add_argument("--all-finished", action="store_true", help="Traite toutes les courses/étapes finies (>=3 résultats).")
        parser.add_argument("--dry-run", action="store_true", help="N'écrit rien, affiche seulement.")

    @transaction.atomic
    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        kind = opts.get("kind")
        unit_id = opts.get("id")
        all_finished = opts.get("all_finished")

        # force la présence des badges
        _get_badges()

        total_created = 0
        total_skipped = 0

        if all_finished:
            finished_one_days = (
                Result.objects.filter(one_day_race__isnull=False)
                .values("one_day_race_id")
                .annotate(c=Count("id"))
                .filter(c__gte=3)
            )
            for row in finished_one_days:
                res = _award_for_unit("one_day", row["one_day_race_id"], dry_run=dry)
                total_created += res.get("created", 0)
                total_skipped += res.get("skipped", 0)

            finished_stages = (
                Result.objects.filter(stage__isnull=False)
                .values("stage_id")
                .annotate(c=Count("id"))
                .filter(c__gte=3)
            )
            for row in finished_stages:
                res = _award_for_unit("stage", row["stage_id"], dry_run=dry)
                total_created += res.get("created", 0)
                total_skipped += res.get("skipped", 0)

        else:
            if not kind or not unit_id:
                raise CommandError("Utilise soit --all-finished, soit --kind one_day|stage --id <id>.")
            res = _award_for_unit(kind, unit_id, dry_run=dry)
            total_created += res.get("created", 0)
            total_skipped += res.get("skipped", 0)

        if dry:
            self.stdout.write(self.style.WARNING("DRY RUN: aucune écriture en base."))

        self.stdout.write(self.style.SUCCESS(
            f"✅ award_badges terminé | créés: {total_created} | ignorés: {total_skipped}"
        ))