from django.core.management.base import BaseCommand
from badges.models import Badge

DEFAULT_BADGES = [
    ("WIN_UNIT", "Vainqueur d’une course/étape", ""),
    ("WIN_TOUR", "Vainqueur d’un tour", ""),
    ("RED_LANTERN_TOUR", "Lanterne rouge", ""),

    ("FIRST_BET", "Premier prono", "Premier Top5 validé"),
    ("SEASON_FULL", "Saison complète", "A parié sur toutes les courses de la saison"),
    ("TOP10_GLOBAL", "Top 10 saison", "Top 10 du classement global"),
    ("SPECIALIST_SPRINT", "Spécialiste sprinteur", "Vainqueur du classement sprinteur d’un tour"),
    ("SPECIALIST_CLIMB", "Spécialiste grimpeur", "Vainqueur du classement grimpeur d’un tour"),
]

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for code, name, desc in DEFAULT_BADGES:
            Badge.objects.update_or_create(code=code, defaults={"name": name, "description": desc})
        self.stdout.write(self.style.SUCCESS("Badges initialisés ✅"))