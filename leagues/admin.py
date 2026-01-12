from django.contrib import admin
from .models import League, LeagueMember

@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "invite_code", "is_private", "created_at")
    search_fields = ("name", "invite_code", "owner__username")

@admin.register(LeagueMember)
class LeagueMemberAdmin(admin.ModelAdmin):
    list_display = ("league", "user", "joined_at")
    search_fields = ("league__name", "user__username")