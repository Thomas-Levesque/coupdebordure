from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Profile
from .choices import (
    COUNTRY_CHOICES, LANGUAGE_CHOICES, TEAM_CHOICES,
    BIKE_BRAND_CHOICES, FAVORITE_RIDER_CHOICES
)

from django_countries.fields import CountryField

###

class SignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, label="Prénom")
    last_name = forms.CharField(max_length=150, required=True, label="Nom")

    email = forms.EmailField(
        required=True,
        label="Email",
        help_text="Email unique (non modifiable)"
    )

    birth_date = forms.DateField(
        required=False,
        label="Date de naissance",
        widget=forms.DateInput(attrs={"type": "date"})
    )

    country = forms.ChoiceField(
        choices=[("", "— Choisir —")] + list(CountryField().choices),
        required=False,
        label="Pays"
    )

    language = forms.ChoiceField(
        choices=[("", "— Choisir —")] + LANGUAGE_CHOICES,
        required=False,
        label="Langue"
    )

    favorite_team = forms.ChoiceField(
        choices=[("", "— Choisir —")] + TEAM_CHOICES,
        required=False,
        label="Équipe préférée"
    )
    favorite_rider_name = forms.ChoiceField(
        choices=[("", "— Choisir —")] + FAVORITE_RIDER_CHOICES,
        required=False,
        label="Coureur préféré"
    )
    favorite_bike_brand = forms.ChoiceField(
        choices=[("", "— Choisir —")] + BIKE_BRAND_CHOICES,
        required=False,
        label="Marque de vélo"
    )

    avatar_choice = forms.ChoiceField(
        choices=Profile.AVATAR_CHOICES,
        required=False,
        label="Avatar (liste)"
    )
    avatar_upload = forms.ImageField(required=False, label="Photo de profil (upload)")

    class Meta:
        model = User
        fields = ("username", "email","first_name", "last_name", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"].strip().lower()
        user.is_active = False

        if commit:
            user.save()
            profile = user.profile

            profile.birth_date = self.cleaned_data.get("birth_date")
            profile.country = self.cleaned_data.get("country", "")
            profile.language = self.cleaned_data.get("language", "")

            profile.favorite_team = self.cleaned_data.get("favorite_team", "")
            profile.favorite_rider_name = self.cleaned_data.get("favorite_rider_name", "")
            profile.favorite_bike_brand = self.cleaned_data.get("favorite_bike_brand", "")

            choice = self.cleaned_data.get("avatar_choice")
            if choice:
                profile.avatar_choice = choice

            upload = self.cleaned_data.get("avatar_upload")
            if upload:
                profile.avatar_upload = upload

            profile.save()
        return user


from django import forms
from .models import NotificationPreference

class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = ("email_results", "email_reminders")
        labels = {
            "email_results": "Recevoir un email quand un résultat est publié",
            "email_reminders": "Recevoir des rappels avant le départ des courses",
        }