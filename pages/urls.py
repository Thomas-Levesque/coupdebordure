from django.urls import path
from . import views
from .views import home_view, mentions_legales_view
from .views import home_view, offline_view, cgu_view, privacy_view, mentions_legales_view, healthz_view

urlpatterns = [
    path("", home_view, name="home"),
    path("offline/", offline_view, name="offline"),
    path("cgu/", cgu_view, name="cgu"),
    path("privacy/", privacy_view, name="privacy"),
    path("mentions_legales/", mentions_legales_view, name="mentions_legales"),
    path("healthz/", views.healthz_view, name="healthz"),
]