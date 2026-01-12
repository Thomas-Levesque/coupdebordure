from django.db import models
from django.utils import timezone
from django.templatetags.static import static

from django.templatetags.static import static

ISO3_TO_ISO2 = {
    "FRA": "FR",
    "ESP": "ES",
    "ITA": "IT",
    "GBR": "GB",
    "USA": "US",
    "NLD": "NL",
    "BEL": "BE",
    "DEU": "DE",
    "CHE": "CH",
    "PRT": "PT",
    "POL": "PL",
    "CZE": "CZ",
    "SVK": "SK",
    "HUN": "HU",
    "AUT": "AT",
    "SUI": "CH",
    "SLO": "SI",
    "AUS": "AU",
    "CHN": "CN",
    "COL": "CO",
    "DEN": "DK",
    "ECU": "EC",
    "ERI": "ER",
    "GER": "DE",
    "KAZ": "KZ",
    "MEX": "MX",
    "NED": "NL",
    "NOR": "NO",
    "NZL": "NZ",
    "POR": "PT",
    "RUS": "RU",
    "URU": "UY",
    # tu peux en rajouter si besoin
}

class Season(models.Model):
    year = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return str(self.year)


class Tour(models.Model):
    """Course à étapes (Tour de Catalogne, Dauphiné, etc.)"""
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="tours")
    name = models.CharField(max_length=120)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to="tour_images/", null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.season.year})"


class Stage(models.Model):
    class StageType(models.TextChoices):
        FLAT = "FLAT", "Plat"
        HILLY = "HILLY", "Vallonnée"
        MOUNTAIN = "MOUNTAIN", "Montagne"
        TT = "TT", "Contre-la-montre"

    tour = models.ForeignKey("races.Tour", on_delete=models.CASCADE, related_name="stages")
    number = models.PositiveIntegerField()
    name = models.CharField(max_length=120)
    start_datetime = models.DateTimeField()
    stage_type = models.CharField(max_length=16, choices=StageType.choices, default=StageType.FLAT)

    # ✅ Nouveau : profil étape
    profile_text = models.TextField(blank=True, default="")
    profile_image = models.ImageField(upload_to="stage_profiles/", null=True, blank=True)

    class Meta:
        unique_together = [("tour", "number")]
        ordering = ["tour", "number"]

    def __str__(self):
        return f"{self.tour.name} - Étape {self.number}"


class OneDayRace(models.Model):
    season = models.ForeignKey("races.Season", on_delete=models.CASCADE, related_name="one_day_races")
    name = models.CharField(max_length=120)
    start_datetime = models.DateTimeField()

    image = models.ImageField(upload_to="race_images/", null=True, blank=True)

    # ✅ Nouveau : profil course
    profile_text = models.TextField(blank=True, default="")
    profile_image = models.ImageField(upload_to="race_profiles/", null=True, blank=True)

    class Meta:
        ordering = ["start_datetime"]

    def __str__(self):
        return f"{self.name} ({self.season.year})"


class Team(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name

class Rider(models.Model):
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    country = models.CharField(max_length=2, blank=True)

    team = models.CharField(max_length=120, blank=True, default="")
    birth_date = models.DateField(null=True, blank=True)

    @property
    def country_iso2(self) -> str:
        if not self.country:
            return ""
        c = self.country.strip().upper()
        if len(c) == 2:
            return c
        return ISO3_TO_ISO2.get(c, "")

    @property
    def flag_url(self) -> str:
        code = self.country_iso2.lower()
        if not code:
            return static("flags/_unknown.svg")
        return static(f"flags/{code}.svg")

    class Meta:
        ordering = ("last_name", "first_name")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Entry(models.Model):
    """
    Engagement d'un coureur dans une unité jouable (OneDayRace OU Stage) avec une cote.
    Exactly one of (one_day_race, stage) must be set.
    """
    one_day_race = models.ForeignKey(OneDayRace, on_delete=models.CASCADE, null=True, blank=True, related_name="entries")
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, null=True, blank=True, related_name="entries")

    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name="entries")
    odds = models.DecimalField(max_digits=4, decimal_places=1)  # ex: 10.0, 9.5, ..., 1.0

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["one_day_race", "rider"], name="uniq_rider_one_day"),
            models.UniqueConstraint(fields=["stage", "rider"], name="uniq_rider_stage"),
        ]

    def clean(self):
        # validation logique
        if (self.one_day_race is None) == (self.stage is None):
            raise ValueError("Entry: set exactly one of one_day_race OR stage.")

    def __str__(self):
        unit = self.one_day_race or self.stage
        return f"{unit} - {self.rider} (odds {self.odds})"


class Result(models.Model):
    """
    Résultat officiel (positions).
    """
    one_day_race = models.ForeignKey(OneDayRace, on_delete=models.CASCADE, null=True, blank=True, related_name="results")
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, null=True, blank=True, related_name="results")

    position = models.PositiveIntegerField()
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name="results")

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["one_day_race", "position"], name="uniq_pos_one_day"),
            models.UniqueConstraint(fields=["stage", "position"], name="uniq_pos_stage"),
            models.UniqueConstraint(fields=["one_day_race", "rider"], name="uniq_rider_result_one_day"),
            models.UniqueConstraint(fields=["stage", "rider"], name="uniq_rider_result_stage"),
        ]

    def clean(self):
        if (self.one_day_race is None) == (self.stage is None):
            raise ValueError("Result: set exactly one of one_day_race OR stage.")

    def __str__(self):
        unit = self.one_day_race or self.stage
        return f"{unit} - #{self.position} {self.rider}"


def unit_start_datetime(one_day_race=None, stage=None):
    if one_day_race:
        return one_day_race.start_datetime
    if stage:
        return stage.start_datetime
    return timezone.now()


from django.db import models

LANG_CHOICES = [
    ("fr", "Français"),
    ("en", "English"),
    ("es", "Español"),
    ("nl", "Nederlands"),
    ("de", "Deutsch"),
    ("it", "Italiano"),
    ("pt", "Português"),
]


class StageTranslation(models.Model):
    stage = models.ForeignKey("races.Stage", on_delete=models.CASCADE, related_name="translations")
    language = models.CharField(max_length=2, choices=LANG_CHOICES)
    profile_text = models.TextField(blank=True, default="")

    class Meta:
        unique_together = [("stage", "language")]
        ordering = ["language"]

    def __str__(self):
        return f"{self.stage} [{self.language}]"


class OneDayRaceTranslation(models.Model):
    race = models.ForeignKey("races.OneDayRace", on_delete=models.CASCADE, related_name="translations")
    language = models.CharField(max_length=2, choices=LANG_CHOICES)
    profile_text = models.TextField(blank=True, default="")

    class Meta:
        unique_together = [("race", "language")]
        ordering = ["language"]

    def __str__(self):
        return f"{self.race} [{self.language}]"