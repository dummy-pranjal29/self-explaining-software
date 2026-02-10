from django.http import JsonResponse
import time
from ses_intelligence.tracing import trace_behavior
from ses_intelligence.runtime_state import get_behavior_graph

@trace_behavior
def save_user():
    time.sleep(0.05)

@trace_behavior
def send_welcome_email():
    time.sleep(0.02)

@trace_behavior
def signup(request):
    save_user()
    send_welcome_email()
    return JsonResponse({"status": "user created"})

def graph_debug(request):
    graph = get_behavior_graph()
    return JsonResponse({
        "behavior_graph": graph.summary()
    })
