import sys
import requests
import argparse
from datetime import datetime

def check_agent_status(server_url, project_id):
    url = f"{server_url.rstrip('/')}/api/v1/agent/list/?project_id={project_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        agents = data.get("agents", [])
        print(f"\nAgent Status for project '{project_id}' at {server_url}:")
        if not agents:
            print("No agents registered or online.")
        else:
            for agent in agents:
                print(f"- Agent ID: {agent.get('agent_id')}")
                print(f"  Name: {agent.get('agent_name')}")
                print(f"  Registered: {agent.get('registered_at')}")
                print(f"  Last Heartbeat: {agent.get('last_heartbeat')}")
                print(f"  Status: {agent.get('status')}")
                print()
        print(f"Checked at {datetime.utcnow().isoformat()} UTC\n")
    except Exception as e:
        print(f"Error checking agent status: {e}")

def main():
    parser = argparse.ArgumentParser(description="Check SES agent status for any server and project.")
    parser.add_argument("--server", required=True, help="SES server URL (e.g. http://localhost:8000 or https://your-app.onrender.com)")
    parser.add_argument("--project-id", default="default", help="Project ID to check (default: default)")
    args = parser.parse_args()
    check_agent_status(args.server, args.project_id)

if __name__ == "__main__":
    main()
import argparse
import requests
import sys

def main():
    parser = argparse.ArgumentParser(description="Check SES agent status on a server.")
    parser.add_argument("--server", required=True, help="SES server base URL (e.g. http://localhost:8000 or https://your-app.onrender.com)")
    parser.add_argument("--project-id", default="default", help="Project ID to check (default: default)")
    args = parser.parse_args()

    url = f"{args.server.rstrip('/')}/api/v1/agent/list/?project_id={args.project_id}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        agents = data.get("agents", [])
        print(f"\nProject: {args.project_id}")
        print(f"Server: {args.server}")
        print(f"Agents found: {len(agents)}\n")
        for agent in agents:
            print(f"Agent ID: {agent['agent_id']}")
            print(f"  Name: {agent['agent_name']}")
            print(f"  Registered: {agent['registered_at']}")
            print(f"  Last Heartbeat: {agent['last_heartbeat']}")
            print(f"  Status: {agent['status']}")
            print()
        if not agents:
            print("No agents registered or sending heartbeats for this project.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
