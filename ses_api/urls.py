from django.urls import path
from . import views

# API v1 endpoints
urlpatterns = [
    # Core intelligence endpoints (require project parameter)
    path("v1/health/", views.api_health, name="api_health"),
    path("v1/forecast/", views.api_forecast, name="api_forecast"),
    path("v1/impact/", views.api_impact, name="api_impact"),
    path("v1/graph/", views.api_graph, name="api_graph"),
    path("v1/executive/", views.api_executive, name="api_executive"),
    
    # Project management endpoints
    path("v1/projects/", views.api_projects_list, name="api_projects_list"),
    path("v1/projects/create/", views.api_project_create, name="api_project_create"),
    path("v1/projects/delete/<str:project_id>/", views.api_project_delete, name="api_project_delete"),
    
    # LLM Chat endpoint
    path("v1/chat/", views.api_chat, name="api_chat"),
    
    # Version redirect (optional - redirects /api/projects/ to /api/v1/projects/)
    path("projects/", views.api_projects_list, name="api_projects_list_legacy"),
]
