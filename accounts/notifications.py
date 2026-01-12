from django.core.mail import send_mail
from django.conf import settings


def _can_email(user, kind: str) -> bool:
    """
    Vérifie si on peut envoyer un email à l'utilisateur.
    kind = "results" | "reminders"
    """

    # 1️⃣ utilisateur inexistant ou email manquant
    if not user or not user.email:
        return False

    # 2️⃣ email non confirmé
    if not user.is_active:
        return False

    # 3️⃣ préférences (si le modèle existe)
    prefs = getattr(user, "notif_prefs", None)
    if prefs:
        if kind == "results" and not prefs.email_results:
            return False
        if kind == "reminders" and not prefs.email_reminders:
            return False

    return True


def notify_result(user, race_name, url=None):
    if not _can_email(user, "results"):
        return

    send_mail(
        subject=f"Résultat publié — {race_name}",
        message=(
            f"Bonjour {user.username},\n\n"
            f"Le résultat de {race_name} est disponible.\n"
            + (f"Lien : {url}\n\n" if url else "\n")
            + "À bientôt sur Coup de Bordure !"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def notify_reminder(user, race_name, start_dt, url=None):
    if not _can_email(user, "reminders"):
        return

    send_mail(
        subject=f"Rappel pronostic — {race_name}",
        message=(
            f"Bonjour {user.username},\n\n"
            f"Pense à valider ton Top5 avant le départ "
            f"({start_dt.strftime('%d/%m/%Y %H:%M')}).\n"
            + (f"Lien : {url}\n\n" if url else "\n")
            + "Bonne chance 🚴"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )