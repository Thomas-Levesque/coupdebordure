# ads/admin.py
from django.contrib import admin
from .models import AdPlacement


@admin.register(AdPlacement)
class AdPlacementAdmin(admin.ModelAdmin):
    list_display = ("slot", "title", "is_active", "priority", "start_at", "end_at")
    list_filter = ("slot", "is_active")
    search_fields = ("title", "target_url")
    ordering = ("slot", "priority", "-created_at")
