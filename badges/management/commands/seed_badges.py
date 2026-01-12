from django.core.management.base import BaseCommand
from badges.models import Badge

DEFAULT_BADGES = [
    # --- unit / résultats ---
    {"code": "WIN_UNIT", "name": "Vainqueur", "description": "Tu as terminé 1er sur une course/étape."},
    {"code": "PODIUM_UNIT", "name": "Podium", "description": "Tu as terminé dans le top 3 sur une course/étape."},
    {"code": "TOP5_UNIT", "name": "Top 5", "description": "Tu as terminé dans le top 5 sur une course/étape."},

    # --- global / participation ---
    {"code": "FIRST_BET", "name": "Premier prono", "description": "Tu as validé ton tout premier Top 5."},

    # --- badges saison 2026 (catalogue) ---
    {"code": "FIRST_UNIT_PLAYED_2026", "name": "Première participation", "description": "Tu as validé au moins un Top5 sur la saison 2026."},
    {"code": "SEASON_FINISHER_2026", "name": "Saison complète", "description": "Tu as participé à toutes les courses d'un jour + au moins 1 étape de chaque tour (2026)."},
    {"code": "MONUMENT_FINISHER_2026", "name": "Monuments", "description": "Tu as participé aux 5 Monuments (2026)."},
    {"code": "GRANDTOUR_FINISHER_2026", "name": "Grands Tours", "description": "Tu as participé aux 3 Grands Tours (2026)."},
]

class Command(BaseCommand):
    help = "Crée (ou met à jour) les badges du catalogue."

    def handle(self, *args, **options):
        created = updated = 0

        for b in DEFAULT_BADGES:
            _, was_created = Badge.objects.update_or_create(
                code=b["code"],
                defaults={"name": b["name"], "description": b["description"]},
            )
            created += int(was_created)
            updated += int(not was_created)

        self.stdout.write(self.style.SUCCESS(
            f"✅ seed_badges terminé | créés: {created} | maj: {updated} | total: {Badge.objects.count()}"
        ))