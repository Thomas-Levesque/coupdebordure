from django.contrib import admin
from django.utils.html import format_html
from .models import Badge, UserBadge

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("icon_preview", "code", "name")
    search_fields = ("code", "name")

    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" style="height:28px;width:28px;object-fit:contain;" />', obj.icon.url)
        return "—"
    icon_preview.short_description = "Icon"

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "awarded_at")
    search_fields = ("user__username", "badge__code", "badge__name")