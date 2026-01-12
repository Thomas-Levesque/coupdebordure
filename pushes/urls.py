from django.urls import path
from .views import vapid_public_key, subscribe

urlpatterns = [
    path("public-key/", vapid_public_key, name="push_public_key"),
    path("subscribe/", subscribe, name="push_subscribe"),
]