import secrets
from django.conf import settings
from django.db import models

class League(models.Model):
    name = models.CharField(max_length=80)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_leagues")
    invite_code = models.CharField(max_length=12, unique=True, db_index=True)
    is_private = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = secrets.token_hex(4)[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.invite_code})"


class LeagueMember(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="league_memberships")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("league", "user")]

    def __str__(self):
        return f"{self.user} in {self.league}"


# leagues/models.py
from django.conf import settings
from django.db import models

class LeagueMessage(models.Model):
    league = models.ForeignKey("League", on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="league_messages")
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.league} - {self.author} - {self.created_at:%Y-%m-%d %H:%M}"