from django import forms
from .models import Profile
from .choices import COUNTRY_CHOICES, LANGUAGE_CHOICES, TEAM_CHOICES, BIKE_BRAND_CHOICES, FAVORITE_RIDER_CHOICES
from badges.models import Badge, UserBadge
from django_countries.fields import CountryField

class ProfileForm(forms.ModelForm):
    country = forms.ChoiceField(
        choices=[("", "— Choisir —")] + list(CountryField().choices),
        required=False,
        label="Pays",
    )
    language = forms.ChoiceField(choices=[("", "— Choisir —")] + LANGUAGE_CHOICES, required=False, label="Langue")
    favorite_team = forms.ChoiceField(choices=[("", "— Choisir —")] + TEAM_CHOICES, required=False, label="Équipe préférée")
    favorite_rider_name = forms.ChoiceField(choices=[("", "— Choisir —")] + FAVORITE_RIDER_CHOICES, required=False, label="Coureur préféré")
    favorite_bike_brand = forms.ChoiceField(choices=[("", "— Choisir —")] + BIKE_BRAND_CHOICES, required=False, label="Marque de vélo")

    featured_badge = forms.ModelChoiceField(
        queryset=Badge.objects.none(),
        required=False,
        empty_label="— Aucun badge affiché —",
        label="Badge à afficher",
    )

    class Meta:
        model = Profile
        fields = [
            "birth_date",
            "country",
            "language",
            "favorite_team",
            "favorite_rider_name",
            "favorite_bike_brand",
            "avatar_choice",
            "avatar_upload",
            "featured_badge",
        ]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtre: uniquement les badges déjà gagnés par l'utilisateur
        if user is not None:
            badge_ids = UserBadge.objects.filter(user=user).values_list("badge_id", flat=True)
            self.fields["featured_badge"].queryset = Badge.objects.filter(id__in=badge_ids).order_by("name")
        else:
            self.fields["featured_badge"].queryset = Badge.objects.none()