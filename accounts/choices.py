# accounts/choices.py

LANGUAGE_CHOICES = [
    ("fr", "Français"),
    ("en", "English"),
    ("es", "Español"),
    ("nl", "Nederlands"),
    ("de", "Deutsch"),
    ("it", "Italiano"),
    ("pt", "Português"),
]

# V1 : liste courte (tu pourras l’étendre)
COUNTRY_CHOICES = [
    ("FR", "France"),
    ("BE", "Belgique"),
    ("CH", "Suisse"),
    ("ES", "Espagne"),
    ("IT", "Italie"),
    ("GB", "Royaume-Uni"),
    ("NL", "Pays-Bas"),
    ("US", "États-Unis"),
]

TEAM_CHOICES = [
    ("UAE", "UAE Team Emirates"),
    ("TVL", "Team Visma | Lease a Bike"),
    ("IGD", "INEOS Grenadiers"),
    ("SOQ", "Soudal Quick-Step"),
    ("TBV", "BORA – hansgrohe"),
    ("LTK", "Lidl–Trek"),
    ("ADC", "Alpecin–Deceuninck"),
]

BIKE_BRAND_CHOICES = [
    ("SPECIALIZED", "Specialized"),
    ("TREK", "Trek"),
    ("CANYON", "Canyon"),
    ("PINARELLO", "Pinarello"),
    ("CERVÉLO", "Cervélo"),
    ("GIANT", "Giant"),
    ("BMC", "BMC"),
]

# V1: coureurs “favoris” en dur (tu pourras remplacer par DB plus tard)
FAVORITE_RIDER_CHOICES = [
    ("POGACAR", "Tadej Pogačar"),
    ("VINGEGAARD", "Jonas Vingegaard"),
    ("VAN_DER_POEL", "Mathieu van der Poel"),
    ("EVENEPOEL", "Remco Evenepoel"),
    ("ROGLIC", "Primož Roglič"),
    ("PIDCOCK", "Tom Pidcock"),
]