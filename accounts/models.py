#accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.templatetags.static import static
from .choices import COUNTRY_CHOICES, LANGUAGE_CHOICES, TEAM_CHOICES, BIKE_BRAND_CHOICES, FAVORITE_RIDER_CHOICES
from django.conf import settings
from django_countries.fields import CountryField
from django.templatetags.static import static

class User(AbstractUser):
    email = models.EmailField(unique=True)

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

class Profile(models.Model):
    AVATAR_CHOICES = [
        ("avatar_1", "Avatar 1"),
        ("avatar_2", "Avatar 2"),
        ("avatar_3", "Avatar 3"),
        ("avatar_4", "Avatar 4"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    birth_date = models.DateField(null=True, blank=True)
    country = CountryField(blank=True)  # stocke un code ISO2 (ex: "FR")
    language = models.CharField(max_length=8, blank=True, choices=LANGUAGE_CHOICES)

    favorite_team = models.CharField(max_length=16, blank=True, choices=TEAM_CHOICES)
    favorite_rider_name = models.CharField(max_length=32, blank=True, choices=FAVORITE_RIDER_CHOICES)
    favorite_bike_brand = models.CharField(max_length=32, blank=True, choices=BIKE_BRAND_CHOICES)

    avatar_choice = models.CharField(
        max_length=32, choices=AVATAR_CHOICES, default="avatar_1"
    )
    avatar_upload = models.ImageField(upload_to="avatars/", null=True, blank=True)

    featured_badge = models.ForeignKey(
        "badges.Badge",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="featured_by",
        verbose_name="Badge affiché"
    )

    def __str__(self):
        return f"Profile({self.user.username})"

    @property
    def avatar_url(self) -> str:
        # Priorité à l’upload
        if self.avatar_upload:
            return self.avatar_upload.url
        # Sinon un fichier statique basé sur le choix
        return static(f"avatars/{self.avatar_choice}.png")

    @property
    def flag_url(self) -> str:
        if not self.country:
            return static("flags/_unknown.svg")
        return static(f"flags/{str(self.country).lower()}.svg")

    @property
    def featured_badge_icon_url(self):
        b = getattr(self, "featured_badge", None)
        if not b:
            return None
        icon = getattr(b, "icon", None)
        if not icon:
            return None
        try:
            return icon.url
        except Exception:
            return None



class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="notif_prefs")
    email_results = models.BooleanField(default=True)
    email_reminders = models.BooleanField(default=True)

    def __str__(self):
        return f"Notifications({self.user.username})"


class ReminderLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    unit_kind = models.CharField(max_length=16)  # "one_day" | "stage"
    unit_id = models.PositiveIntegerField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "unit_kind", "unit_id")