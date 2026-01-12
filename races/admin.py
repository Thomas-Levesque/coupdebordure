from django.contrib import admin
from .models import Season, Tour, Stage, OneDayRace, Rider, Entry, Result

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("year",)

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ("name", "season", "start_datetime", "end_datetime")
    list_filter = ("season",)

from django.contrib import admin
from .models import Stage, OneDayRace, StageTranslation, OneDayRaceTranslation


class StageTranslationInline(admin.TabularInline):
    model = StageTranslation
    extra = 0
    fields = ("language", "profile_text")
    ordering = ("language",)


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ("tour", "number", "name", "start_datetime", "stage_type")
    list_filter = ("tour", "stage_type")
    search_fields = ("name", "tour__name")
    fields = ("tour", "number", "name", "start_datetime", "stage_type", "profile_text", "profile_image")
    inlines = [StageTranslationInline]


class OneDayRaceTranslationInline(admin.TabularInline):
    model = OneDayRaceTranslation
    extra = 0
    fields = ("language", "profile_text")
    ordering = ("language",)


@admin.register(OneDayRace)
class OneDayRaceAdmin(admin.ModelAdmin):
    list_display = ("name", "season", "start_datetime")
    search_fields = ("name",)
    list_filter = ("season",)
    fields = ("season", "name", "start_datetime", "image", "profile_text", "profile_image")
    inlines = [OneDayRaceTranslationInline]

@admin.register(Rider)
class RiderAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "country")
    list_filter = ("country",)
    search_fields = ("first_name", "last_name")
    ordering = ("last_name", "first_name")  # ✅ explicite

@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("rider", "odds", "one_day_race", "stage")
    list_filter = ("one_day_race", "stage")
    search_fields = ("rider__first_name", "rider__last_name")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "rider":
            kwargs["queryset"] = Rider.objects.order_by("last_name", "first_name")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("position", "rider", "one_day_race", "stage")
    list_filter = ("one_day_race", "stage")
    ordering = ("one_day_race", "stage", "position")
