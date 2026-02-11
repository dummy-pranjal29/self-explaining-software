from django.urls import path
from .views import behavior_diff_view, behavior_history_view

urlpatterns = [
    path("debug/behavior-diff/", behavior_diff_view),
    path("debug/behavior-history/", behavior_history_view),
]
