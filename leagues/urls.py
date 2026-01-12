from django.urls import path
from .views import leagues_home, league_create, league_join, league_detail
from .leaderboards import league_leaderboard_global

urlpatterns = [
    path("leagues/", leagues_home, name="leagues_home"),
    path("leagues/create/", league_create, name="league_create"),
    path("leagues/join/", league_join, name="league_join"),
    path("leagues/<int:league_id>/", league_detail, name="league_detail"),
    path("leagues/<int:league_id>/leaderboard/<int:season_year>/", league_leaderboard_global, name="league_lb_global"),
]