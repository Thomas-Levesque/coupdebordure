from django.contrib import admin

# Register your models here.
# accounts/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

import csv
from django.http import HttpResponse

def export_profiles_csv(modeladmin, request, queryset):
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="profiles.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow([
        "username",
        "first_name",
        "last_name",
        "email",
        "birth_date",
        "country",
        "language",
        "favorite_rider",
        "favorite_bike_brand",
        "featured_badge",
    ])

    queryset = queryset.select_related("user", "featured_badge")

    for p in queryset:
        writer.writerow([
            p.user.username,
            p.user.first_name,
            p.user.last_name,
            p.user.email,
            p.birth_date,
            p.country,
            p.language,
            p.favorite_rider_name,
            p.favorite_bike_brand,
            p.featured_badge.name if p.featured_badge else "",
        ])

    return response

export_profiles_csv.short_description = "📥 Exporter les profils sélectionnés (CSV)"

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user", "country", "birth_date",
        "favorite_rider_name", "favorite_bike_brand",
        "favorite_team", "language",
    )
    list_select_related = ("user", "featured_badge")
    search_fields = (
        "user__username", "user__email",
        "user__first_name", "user__last_name",
        "favorite_rider_name", "favorite_bike_brand",
    )
    list_filter = ("country", "language", "favorite_team")
    actions = [export_profiles_csv]