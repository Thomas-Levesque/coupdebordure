from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile

@receiver(post_save, sender=User)
def create_profile(sender, instance: User, created: bool, **kwargs):
    if created:
        Profile.objects.create(user=instance)


from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import NotificationPreference

User = get_user_model()

@receiver(post_save, sender=User)
def create_notification_prefs(sender, instance, created, **kwargs):
    if created:
        NotificationPreference.objects.create(user=instance)