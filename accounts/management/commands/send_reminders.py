from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from accounts.models import ReminderLog, NotificationPreference
from accounts.notifications import notify_reminder

from races.models import OneDayRace, Stage
from bets.models import Bet


class Command(BaseCommand):
    help = "Envoie des rappels Top5 (< 24h avant départ) — 1 rappel max par user/unité."

    def add_arguments(self, parser):
        parser.add_argument("--hours", type=int, default=24, help="Fenêtre (heures) avant départ. Défaut=24")
        parser.add_argument("--dry-run", action="store_true", help="Affiche sans envoyer ni logger")

    def handle(self, *args, **opts):
        hours = opts["hours"]
        dry = opts["dry_run"]

        now = timezone.now()
        limit = now + timedelta(hours=hours)

        User = get_user_model()

        # Users éligibles (email + confirmés)
        users = (
            User.objects
            .filter(is_active=True)
            .exclude(email__isnull=True)
            .exclude(email="")
            .select_related("notif_prefs")
        )

        sent = 0
        candidates = 0

        # ==========================
        # COURSES D’UN JOUR
        # ==========================
        races = OneDayRace.objects.filter(start_datetime__gt=now, start_datetime__lte=limit).order_by("start_datetime")

        for race in races:
            # users ayant déjà validé un Top5
            already = set(
                Bet.objects.filter(one_day_race=race)
                .exclude(submitted_at__isnull=True)
                .values_list("user_id", flat=True)
            )

            for u in users:
                prefs = getattr(u, "notif_prefs", None)
                if prefs and not prefs.email_reminders:
                    continue
                if u.id in already:
                    continue
                if ReminderLog.objects.filter(user=u, unit_kind="one_day", unit_id=race.id).exists():
                    continue

                candidates += 1

                # nom course (adapte si ton champ partials’appelle autrement)
                race_name = getattr(race, "name", str(race))

                if dry:
                    self.stdout.write(f"[DRY] one_day | {race_name} | {u.username}")
                    continue

                notify_reminder(u, race_name, race.start_datetime, url=None)
                ReminderLog.objects.create(user=u, unit_kind="one_day", unit_id=race.id)
                sent += 1

        # ==========================
        # ÉTAPES
        # ==========================
        stages = Stage.objects.filter(start_datetime__gt=now, start_datetime__lte=limit).select_related("tour").order_by("start_datetime")

        for stage in stages:
            already = set(
                Bet.objects.filter(stage=stage)
                .exclude(submitted_at__isnull=True)
                .values_list("user_id", flat=True)
            )

            for u in users:
                prefs = getattr(u, "notif_prefs", None)
                if prefs and not prefs.email_reminders:
                    continue
                if u.id in already:
                    continue
                if ReminderLog.objects.filter(user=u, unit_kind="stage", unit_id=stage.id).exists():
                    continue

                candidates += 1

                tour_name = getattr(stage.tour, "name", "Tour")
                stage_number = getattr(stage, "number", "")
                label = f"{tour_name} — Étape {stage_number}".strip()

                if dry:
                    self.stdout.write(f"[DRY] stage | {label} | {u.username}")
                    continue

                notify_reminder(u, label, stage.start_datetime, url=None)
                ReminderLog.objects.create(user=u, unit_kind="stage", unit_id=stage.id)
                sent += 1

        self.stdout.write(self.style.SUCCESS(
            f"Rappels: candidats={candidates} | envoyés={sent} | fenêtre={hours}h | dry_run={dry}"
        ))