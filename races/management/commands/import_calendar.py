import csv
import re
from datetime import datetime, time
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from races.models import Season, Tour, Stage, OneDayRace


def _parse_date(s: str):
    s = (s or "").strip()
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%d").date()


def _aware_dt(d, t: time):
    tz = timezone.get_current_timezone()
    return timezone.make_aware(datetime.combine(d, t), tz)


def _parse_hhmm(value: str, default: time) -> time:
    s = (value or "").strip().lower()
    if not s:
        return default
    s = s.replace("h", ":")
    m = re.match(r"^(\d{1,2})(?::(\d{1,2}))?$", s)
    if not m:
        return default
    h = int(m.group(1))
    mn = int(m.group(2) or 0)
    if not (0 <= h <= 23 and 0 <= mn <= 59):
        return default
    return time(h, mn)


class Command(BaseCommand):
    help = "Importe le calendrier WorldTour (CSV) vers Season / Tour / OneDayRace (+ options étapes)."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Chemin du CSV")
        parser.add_argument("--year", type=int, help="Saison (ex: 2026)")
        parser.add_argument("--season", type=int, help="Alias de --year")
        parser.add_argument("--dry-run", action="store_true", help="Simulation (aucune écriture)")
        parser.add_argument("--update", action="store_true", help="Met à jour les courses existantes")

        parser.add_argument("--start-time", default="12:00", help="Heure par défaut HH:MM")
        parser.add_argument("--end-time", default="18:00", help="Heure fin par défaut HH:MM")

        parser.add_argument("--create-stages", action="store_true", help="Créer les étapes 1..N")
        parser.add_argument("--force-stages", action="store_true", help="Supprimer/recréer les étapes")

    @transaction.atomic
    def handle(self, *args, **opts):
        file_path = Path(opts["file"])
        if not file_path.exists():
            raise CommandError(f"Fichier introuvable: {file_path}")

        year = opts.get("season") or opts.get("year")
        if not year:
            raise CommandError("Merci de préciser --year ou --season")

        start_t = _parse_hhmm(opts.get("start_time"), default=time(12, 0))
        end_t = _parse_hhmm(opts.get("end_time"), default=time(18, 0))

        season, _ = Season.objects.get_or_create(year=year)

        created_tours = created_one_days = updated = skipped = 0
        planned = []

        with file_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            required = {"kind", "name", "start_date", "end_date", "stages"}
            if not required.issubset(reader.fieldnames or []):
                raise CommandError(
                    f"Colonnes requises: {sorted(required)} | Trouvées: {reader.fieldnames}"
                )

            for row in reader:
                kind = (row.get("kind") or "").strip()
                name = (row.get("name") or "").strip()
                if not kind or not name:
                    continue

                start_date = _parse_date(row.get("start_date"))
                end_date = _parse_date(row.get("end_date"))
                stages_n = int((row.get("stages") or "0").strip() or 0)

                if not start_date:
                    skipped += 1
                    continue

                start_dt = _aware_dt(start_date, start_t)
                end_dt = _aware_dt(end_date, end_t) if end_date else None

                if kind == "one_day":
                    obj, created = OneDayRace.objects.get_or_create(
                        season=season,
                        name=name,
                        defaults={"start_datetime": start_dt},
                    )
                    if created:
                        created_one_days += 1
                        planned.append(f"CREATE one-day {name}")
                    elif opts["update"] and obj.start_datetime != start_dt:
                        obj.start_datetime = start_dt
                        obj.save(update_fields=["start_datetime"])
                        updated += 1
                        planned.append(f"UPDATE one-day {name}")
                    else:
                        skipped += 1

                elif kind == "tour":
                    obj, created = Tour.objects.get_or_create(
                        season=season,
                        name=name,
                        defaults={"start_datetime": start_dt, "end_datetime": end_dt},
                    )
                    if created:
                        created_tours += 1
                        planned.append(f"CREATE tour {name}")
                    elif opts["update"]:
                        changed = False
                        if obj.start_datetime != start_dt:
                            obj.start_datetime = start_dt
                            changed = True
                        if end_dt and obj.end_datetime != end_dt:
                            obj.end_datetime = end_dt
                            changed = True
                        if changed:
                            obj.save(update_fields=["start_datetime", "end_datetime"])
                            updated += 1
                            planned.append(f"UPDATE tour {name}")
                        else:
                            skipped += 1
                    else:
                        skipped += 1

                    # ✅ FIX ICI : create_stages / force_stages
                    if opts["create_stages"] and stages_n > 0:
                        qs = Stage.objects.filter(tour=obj)
                        if qs.exists() and not opts["force_stages"]:
                            planned.append(f"SKIP stages {name} (déjà existantes)")
                        else:
                            if qs.exists() and opts["force_stages"]:
                                qs.delete()

                            for i in range(1, stages_n + 1):
                                Stage.objects.update_or_create(
                                    tour=obj,
                                    number=i,
                                    defaults={
                                        "name": f"Étape {i}",
                                        "start_datetime": obj.start_datetime,
                                        "stage_type": Stage.StageType.FLAT,
                                    },
                                )
                            planned.append(f"CREATE stages 1..{stages_n} {name}")

                else:
                    skipped += 1

        if opts["dry_run"]:
            for p in planned:
                self.stdout.write(p)
            self.stdout.write(self.style.WARNING("DRY-RUN : aucune écriture"))
            raise transaction.TransactionManagementError("Dry run rollback")

        self.stdout.write(self.style.SUCCESS("✅ Import calendrier terminé"))
        self.stdout.write(
            f"Saison {season.year} | tours: {created_tours} | one-day: {created_one_days} | "
            f"maj: {updated} | ignorées: {skipped}"
        )