from django.contrib import admin
from django.urls import path
from demo_app.views import signup, graph_debug

urlpatterns = [
    path("admin/", admin.site.urls),
    path("signup/", signup),
    path("debug/graph/", graph_debug),
]
