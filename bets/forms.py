from django import forms
from races.models import Entry
from .models import Bet

class BetForm(forms.ModelForm):
    class Meta:
        model = Bet
        fields = ["pick1", "pick2", "pick3", "pick4", "pick5"]

    def __init__(self, *args, one_day_race=None, stage=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Remplit les choix avec uniquement les engagés + ordre par cote (favoris en haut)
        entries = Entry.objects.filter(one_day_race=one_day_race, stage=stage).select_related("rider").order_by("-odds", "rider__last_name")
        riders = [e.rider for e in entries]
        for f in self.fields.values():
            f.queryset = type(riders[0]).objects.filter(id__in=[r.id for r in riders]) if riders else f.queryset.none()

        self._one_day_race = one_day_race
        self._stage = stage

    def clean(self):
        cleaned = super().clean()
        picks = [cleaned.get("pick1"), cleaned.get("pick2"), cleaned.get("pick3"), cleaned.get("pick4"), cleaned.get("pick5")]
        picks = [p for p in picks if p is not None]
        if len(picks) != 5:
            raise forms.ValidationError("Merci de sélectionner 5 coureurs.")
        if len(set([p.id for p in picks])) != 5:
            raise forms.ValidationError("Un coureur ne peut être sélectionné qu'une seule fois.")
        return cleaned