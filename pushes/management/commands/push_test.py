from django.core.management.base import BaseCommand
from pushes.models import PushSubscription
from pushes.sender import send_push

class Command(BaseCommand):
    help = "Envoie une notification push de test au dernier abonnement."

    def handle(self, *args, **kwargs):
        sub = PushSubscription.objects.order_by("-id").first()
        if not sub:
            self.stdout.write("Aucune subscription en base. Active les push sur le dashboard.")
            return

        ok = send_push(sub, {
            "title": "Coup de Bordure",
            "body": "✅ Push test reçue !",
            "url": "/dashboard/",
        })
        self.stdout.write("OK" if ok else "ECHEC")