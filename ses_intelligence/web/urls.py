"""
SES Intelligence Web URL Configuration

URL routing for the embedded Django server.
"""

from django.urls import path
from . import views

# API v1 endpoints
urlpatterns = [
    # Core intelligence endpoints (require project parameter)
    path("api/v1/health/", views.api_health, name="api_health"),
    path("api/v1/forecast/", views.api_forecast, name="api_forecast"),
    path("api/v1/impact/", views.api_impact, name="api_impact"),
    path("api/v1/graph/", views.api_graph, name="api_graph"),
    path("api/v1/executive/", views.api_executive, name="api_executive"),
    
    # Project management endpoints
    path("api/v1/projects/", views.api_projects_list, name="api_projects_list"),
    path("api/v1/projects/create/", views.api_project_create, name="api_project_create"),
    path("api/v1/projects/delete/<str:project_id>/", views.api_project_delete, name="api_project_delete"),
    
    # LLM Chat endpoint
    path("api/v1/chat/", views.api_chat, name="api_chat"),
    
    # UI Config endpoint
    path("api/v1/config/", views.api_config, name="api_config"),
    
    # Remote Agent endpoints
    path("api/v1/agent/register/", views.api_agent_register, name="api_agent_register"),
    path("api/v1/agent/heartbeat/", views.api_agent_heartbeat, name="api_agent_heartbeat"),
    path("api/v1/agent/list/", views.api_agent_list, name="api_agent_list"),
    path("api/v1/agent/unregister/", views.api_agent_unregister, name="api_agent_unregister"),
    
    # Legacy endpoints (without v1 prefix)
    path("api/projects/", views.api_projects_list, name="api_projects_list_legacy"),
    path("api/health/", views.api_health, name="api_health_legacy"),
    path("api/forecast/", views.api_forecast, name="api_forecast_legacy"),
    path("api/impact/", views.api_impact, name="api_impact_legacy"),
    path("api/graph/", views.api_graph, name="api_graph_legacy"),
    path("api/executive/", views.api_executive, name="api_executive_legacy"),
    path("api/chat/", views.api_chat, name="api_chat_legacy"),
]

# Static file serving
from django.conf import settings
from django.conf.urls.static import static

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# Catch-all for SPA - must be last
urlpatterns += [
    # Serve React app for all other routes (SPA fallback)
    path("", views.serve_index, name="serve_index"),
]
