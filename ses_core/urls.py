from django.contrib import admin
from django.urls import path

from demo_app.views import (
    signup,
    graph_debug,
    behavior_diff_debug,
    behavior_history_debug,
    anomaly_debug,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Application endpoints
    path("signup/", signup),

    # Debug / introspection endpoints
    path("debug/graph/", graph_debug),
    path("debug/behavior-diff/", behavior_diff_debug),
    path("debug/behavior-history/", behavior_history_debug),
    path("debug/anomalies/", anomaly_debug),
]
