# ads/models.py
from django.db import models
from django.utils import timezone


class AdPlacement(models.Model):
    class Slot(models.TextChoices):
        TOP = "top", "Haut"
        SIDEBAR = "sidebar", "Sidebar"
        BOTTOM = "bottom", "Bas"

    slot = models.CharField(max_length=16, choices=Slot.choices, db_index=True)
    title = models.CharField(max_length=120, blank=True)
    image = models.ImageField(upload_to="ads/", null=True, blank=True)
    target_url = models.URLField(blank=True)

    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.PositiveIntegerField(default=100, db_index=True)

    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("slot", "priority", "-created_at")

    def __str__(self):
        return f"{self.slot} • {self.title or 'Ad'}"

    def is_live(self) -> bool:
        if not self.is_active:
            return False
        now = timezone.now()
        if self.start_at and now < self.start_at:
            return False
        if self.end_at and now > self.end_at:
            return False
        return True