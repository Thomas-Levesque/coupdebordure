from django.urls import path
from .views import races_list_view, one_day_detail_view, stage_detail_view

urlpatterns = [
    path("races/", races_list_view, name="races_list"),
    path("races/one-day/<int:race_id>/", one_day_detail_view, name="one_day_detail"),
    path("races/stage/<int:stage_id>/", stage_detail_view, name="stage_detail"),
]