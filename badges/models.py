from django.conf import settings
from django.db import models
from django.templatetags.static import static

class Badge(models.Model):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)

    icon = models.ImageField(
        upload_to="badge_icons/",
        null=True, blank=True,
        help_text="PNG/SVG (si SVG: vérifier config)."
    )

    @property
    def icon_url(self) -> str:
        # 1) upload (media)
        if self.icon:
            try:
                return self.icon.url
            except Exception:
                pass

        # 2) fallback static : static/badges/<code>.svg
        code = (self.code or "").strip().lower()
        return static(f"badges/{code}.svg") if code else static("badges/_unknown.svg")

    def __str__(self):
        return self.name

class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="awards")
    awarded_at = models.DateTimeField(auto_now_add=True)
    context = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "badge"], name="uniq_user_badge")
        ]
        indexes = [
            models.Index(fields=["user", "badge"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.badge}"