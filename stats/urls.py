from django.urls import path
from .views import my_stats_view

urlpatterns = [
    path("stats/", my_stats_view, name="my_stats"),
]