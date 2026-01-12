from django import forms
from .models import League

class LeagueCreateForm(forms.ModelForm):
    class Meta:
        model = League
        fields = ["name", "is_private"]

class LeagueJoinForm(forms.Form):
    invite_code = forms.CharField(max_length=12, label="Code d’invitation")


# leagues/forms.py
from django import forms
from .models import LeagueMessage

class LeagueMessageForm(forms.ModelForm):
    class Meta:
        model = LeagueMessage
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Écrire un message…",
                "style": "width:100%;"
            })
        }