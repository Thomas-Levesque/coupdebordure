from django.urls import path
from .views import bet_for_one_day_view, bet_for_stage_view
from .leaderboards import (
    global_leaderboard,
    unit_leaderboard_one_day,
    unit_leaderboard_stage,
    tour_leaderboard,
)
from .leaderboards import tour_special_leaderboard
from .leaderboards import leaderboards_hub

urlpatterns = [
    # Bets
    path("bet/one-day/<int:race_id>/", bet_for_one_day_view, name="bet_one_day"),
    path("bet/stage/<int:stage_id>/", bet_for_stage_view, name="bet_stage"),

    # Leaderboards
    path("leaderboards/global/<int:season_year>/", global_leaderboard, name="lb_global"),
    path("leaderboards/one-day/<int:race_id>/", unit_leaderboard_one_day, name="lb_one_day"),
    path("leaderboards/stage/<int:stage_id>/", unit_leaderboard_stage, name="lb_stage"),
    path("leaderboards/tour/<int:tour_id>/", tour_leaderboard, name="lb_tour"),
    path("leaderboards/tour/<int:tour_id>/<str:category>/", tour_special_leaderboard, name="lb_tour_special"),
    path("leaderboards/", leaderboards_hub, name="leaderboards_hub"),
]

