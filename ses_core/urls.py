from django.contrib import admin
from django.urls import path
from demo_app.views import signup

urlpatterns = [
    path("admin/", admin.site.urls),
    path("signup/", signup),
]
