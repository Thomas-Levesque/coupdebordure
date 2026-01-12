import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction

from races.models import Rider


def parse_date(s: str):
    s = (s or "").strip()
    if not s:
        return None
    # attend YYYY-MM-DD
    return datetime.strptime(s, "%Y-%m-%d").date()


class Command(BaseCommand):
    help = "Importe des coureurs depuis un CSV (export Excel). Relançable sans doublons."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Chemin vers le fichier CSV (UTF-8).")
        parser.add_argument("--dry-run", action="store_true", help="N'écrit rien en base.")
        parser.add_argument("--update-only", action="store_true", help="Met à jour uniquement, ne crée pas de nouveaux riders.")

    @transaction.atomic
    def handle(self, *args, **opts):
        path = opts["file"]
        dry = opts["dry_run"]
        update_only = opts["update_only"]

        created = 0
        updated = 0
        skipped = 0

        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            required = {"first_name", "last_name", "country", "birth_date", "team"}
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise SystemExit(f"Colonnes manquantes dans CSV: {sorted(missing)}")

            for row in reader:
                first = (row.get("first_name") or "").strip()
                last = (row.get("last_name") or "").strip()
                if not first or not last:
                    skipped += 1
                    continue

                country = (row.get("country") or "").strip()
                team = (row.get("team") or "").strip()
                birth_date = parse_date(row.get("birth_date"))

                if dry:
                    self.stdout.write(f"[DRY] {first} {last} | {country} | {birth_date} | {team}")
                    continue

                # Clé de dédoublonnage:
                # - si birth_date dispo: (first,last,birth_date)
                # - sinon fallback: (first,last)
                lookup = {"first_name": first, "last_name": last}
                if birth_date:
                    lookup["birth_date"] = birth_date

                exists = Rider.objects.filter(**lookup).exists()
                if update_only and not exists:
                    skipped += 1
                    continue

                obj, was_created = Rider.objects.update_or_create(
                    **lookup,
                    defaults={
                        "country": country,
                        "team": team,
                        "birth_date": birth_date,
                        "first_name": first,
                        "last_name": last,
                    },
                )

                if was_created:
                    created += 1
                else:
                    updated += 1

        if dry:
            self.stdout.write(self.style.WARNING("DRY RUN terminé (aucune écriture)."))
        self.stdout.write(self.style.SUCCESS(
            f"Import riders terminé ✅ created={created} updated={updated} skipped={skipped}"
        ))