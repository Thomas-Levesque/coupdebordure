from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.shortcuts import get_object_or_404

from races.models import Season
from bets.models import BetScore
from badges.services import award_badge, user_id_to_user


class Command(BaseCommand):
    help = "Attribue le badge TOP10_GLOBAL pour une saison (à lancer manuellement, sans spam)."

    def add_arguments(self, parser):
        parser.add_argument("--year", type=int, required=True)

    def handle(self, *args, **opts):
        year = opts["year"]
        season = get_object_or_404(Season, year=year)

        qs1 = (
            BetScore.objects.filter(bet__one_day_race__season=season)
            .values("bet__user_id", "bet__user__username")
            .annotate(total=Sum("score"))
        )
        qs2 = (
            BetScore.objects.filter(bet__stage__tour__season=season)
            .values("bet__user_id", "bet__user__username")
            .annotate(total=Sum("score"))
        )

        totals = {}
        for row in list(qs1) + list(qs2):
            key = (row["bet__user_id"], row["bet__user__username"])
            totals[key] = totals.get(key, 0) + float(row["total"] or 0)

        rows = [{"user_id": k[0], "username": k[1], "total": v} for k, v in totals.items()]
        rows.sort(key=lambda r: (-r["total"], r["username"]))

        count = 0
        for r in rows[:10]:
            award_badge(user_id_to_user(r["user_id"]), "TOP10_GLOBAL", {"season": season.year})
            count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ TOP10_GLOBAL attribué pour {year} (top {count})"))