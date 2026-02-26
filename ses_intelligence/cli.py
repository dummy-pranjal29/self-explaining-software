"""
SES Intelligence CLI

A command-line interface for the Self-Evolving Software Intelligence platform.

Usage:
    ses init [--project-id <id>]
    ses snapshot [--project-id <id>]
    ses forecast [--project-id <id>]
    ses health [--project-id <id>]
    ses status
    ses doctor
"""

import argparse
import sys
from typing import Optional

from ses_intelligence import initialize, get_runtime_snapshots, is_initialized, get_config
from ses_intelligence.architecture_health.engine import ArchitectureHealthEngine
from ses_intelligence.architecture_health.forecasting import ArchitectureHealthForecaster


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="ses",
        description="Self-Evolving Software Intelligence CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    ses init --project-id my-app
    ses snapshot
    ses forecast
    ses health
    ses status
    ses doctor
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # init command
    init_parser = subparsers.add_parser("init", help="Initialize SES for a project")
    init_parser.add_argument(
        "--project-id", 
        default="default",
        help="Project ID (default: default)"
    )
    init_parser.add_argument(
        "--storage-path",
        help="Custom storage path"
    )
    
    # snapshot command
    snapshot_parser = subparsers.add_parser("snapshot", help="Take a runtime snapshot")
    snapshot_parser.add_argument(
        "--project-id",
        default="default",
        help="Project ID (default: default)"
    )
    
    # forecast command
    forecast_parser = subparsers.add_parser("forecast", help="Run forecasting")
    forecast_parser.add_argument(
        "--project-id",
        default="default",
        help="Project ID (default: default)"
    )
    forecast_parser.add_argument(
        "--horizon",
        type=int,
        default=5,
        help="Forecast horizon (default: 5)"
    )
    
    # health command
    health_parser = subparsers.add_parser("health", help="Check architecture health")
    health_parser.add_argument(
        "--project-id",
        default="default",
        help="Project ID (default: default)"
    )
    
    # status command
    status_parser = subparsers.add_parser("status", help="Show SES status")
    
    # doctor command
    doctor_parser = subparsers.add_parser("doctor", help="Run diagnostics and show system status")
    
    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start the SES Intelligence web dashboard")
    serve_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    serve_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser automatically"
    )
    
    # agent command - run local agent to send data to remote server
    agent_parser = subparsers.add_parser("agent", help="Run local agent to send data to remote server")
    agent_parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="Remote server URL (default: http://localhost:8000)"
    )
    agent_parser.add_argument(
        "--project-id",
        default="default",
        help="Project ID to send data to (default: default)"
    )
    agent_parser.add_argument(
        "--agent-id",
        default=None,
        help="Custom agent ID (default: auto-generated)"
    )
    agent_parser.add_argument(
        "--agent-name",
        default="Local Machine",
        help="Agent name for display (default: Local Machine)"
    )
    agent_parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Heartbeat interval in seconds (default: 30)"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == "init":
        cmd_init(args)
    elif args.command == "snapshot":
        cmd_snapshot(args)
    elif args.command == "forecast":
        cmd_forecast(args)
    elif args.command == "health":
        cmd_health(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "doctor":
        cmd_doctor(args)
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "agent":
        cmd_agent(args)
    else:
        parser.print_help()


def cmd_init(args):
    """Initialize SES for a project."""
    config = initialize(
        project_id=args.project_id,
        storage_path=args.storage_path,
    )
    print(f"✓ SES initialized for project: {args.project_id}")
    print(f"  Storage: {config.storage_path or 'default'}")
    print(f"  Forecasting: {'enabled' if config.enable_forecasting else 'disabled'}")
    print(f"  Narratives: {'enabled' if config.enable_narratives else 'disabled'}")


def cmd_snapshot(args):
    """Take a runtime snapshot."""
    initialize(project_id=args.project_id)
    snapshots = get_runtime_snapshots(project_id=args.project_id)
    
    if not snapshots:
        print("No snapshots available.")
        return
    
    latest = snapshots[-1]
    print(f"✓ Snapshot taken: {latest.snapshot_id}")
    print(f"  Nodes: {latest.graph.number_of_nodes()}")
    print(f"  Edges: {latest.graph.number_of_edges()}")


def cmd_forecast(args):
    """Run forecasting."""
    initialize(project_id=args.project_id)
    snapshots = get_runtime_snapshots(project_id=args.project_id)
    
    if not snapshots:
        print("No data available for forecasting. Run some code first!")
        return
    
    forecast_engine = ArchitectureHealthForecaster()
    forecast = forecast_engine.forecast(steps_ahead=args.horizon)
    
    print(f"✓ Forecast generated (horizon: {args.horizon})")
    predictions = forecast.get("forecast", [])
    for i, pred in enumerate(predictions):
        print(f"  Step {i+1}: {pred.get('health_score', 'N/A')}")


def cmd_health(args):
    """Check architecture health."""
    initialize(project_id=args.project_id)
    snapshots = get_runtime_snapshots(project_id=args.project_id)
    
    if not snapshots:
        print("No data available. Run some code first!")
        return
    
    health_engine = ArchitectureHealthEngine()
    health = health_engine.compute()
    
    print(f"✓ Architecture Health Report")
    print(f"  Overall Score: {health.get('overall_score', 0):.1f}/100")
    print(f"  Stability: {health.get('stability_index', 0):.2f}")
    print(f"  Risk Level: {health.get('risk_level', 'unknown')}")
    
    recommendations = health.get("recommendations", [])
    if recommendations:
        print("  Recommendations:")
        for rec in recommendations[:3]:
            print(f"    - {rec}")


def cmd_status(args):
    """Show SES status."""
    if not is_initialized():
        print("✗ SES not initialized")
        print("  Run: ses init --project-id <your-project>")
        return
    
    config = get_config()
    print(f"✓ SES Status")
    print(f"  Project: {config.project_id}")
    print(f"  Storage: {config.storage_path or 'default'}")
    print(f"  Forecasting: {'✓' if config.enable_forecasting else '✗'}")
    print(f"  Narratives: {'✓' if config.enable_narratives else '✗'}")
    print(f"  LLM: {'✓' if config.llm_api_key else '✗'}")


def cmd_doctor(args):
    """Run diagnostics and show detailed system status."""
    import os
    
    # Get SDK version
    try:
        from ses_intelligence import __version__ as sdk_version
    except ImportError:
        sdk_version = "1.0.0b0"
    
    print("=" * 50)
    print("SES Intelligence - Diagnostic Report")
    print("=" * 50)
    
    # SDK version
    print(f"\n📦 SDK Version: {sdk_version}")
    
    # Project ID
    if not is_initialized():
        print(f"⚠️  Project ID: Not initialized")
        print(f"   Run: ses init --project-id <your-project>")
        return
    
    config = get_config()
    print(f"📁 Project ID: {config.project_id}")
    
    # Snapshot count
    snapshots = get_runtime_snapshots(project_id=config.project_id)
    snapshot_count = len(snapshots)
    print(f"📸 Snapshot Count: {snapshot_count}")
    
    # Latest health score
    if snapshot_count > 0:
        health_engine = ArchitectureHealthEngine()
        health = health_engine.compute()
        health_score = health.get('overall_score', 0)
        print(f"💚 Latest Health Score: {health_score:.1f}/100")
    else:
        print(f"💚 Latest Health Score: N/A (no snapshots)")
    
    # Forecast direction
    if snapshot_count >= 3:
        forecast_engine = ArchitectureHealthForecaster()
        forecast = forecast_engine.forecast(steps_ahead=3)
        forecast_direction = forecast.get("direction", "unknown")
        print(f"🔮 Forecast Direction: {forecast_direction}")
    else:
        print(f"🔮 Forecast Direction: N/A (need more snapshots)")
    
    # Storage mode
    storage_mode = "custom" if config.storage_path else "default"
    print(f"💾 Storage Mode: {storage_mode}")
    if config.storage_path:
        print(f"   Path: {config.storage_path}")
    
    # LLM enabled status
    llm_enabled = bool(config.llm_api_key or os.environ.get('OPENAI_API_KEY'))
    print(f"🤖 LLM Enabled: {'Yes' if llm_enabled else 'No'}")
    if config.llm_model:
        print(f"   Model: {config.llm_model}")
    
    print("\n" + "=" * 50)


def cmd_serve(args):
    """Start the SES Intelligence web dashboard server."""
    from ses_intelligence.web.server import run_server
    
    # Determine whether to open browser
    open_browser = not args.no_browser
    
    print("=" * 50)
    print("Starting SES Intelligence Dashboard")
    print("=" * 50)
    print(f"Server will be available at: http://{args.host}:{args.port}")
    if open_browser:
        print("Browser will open automatically...")
    print("=" * 50)
    
    run_server(
        host=args.host,
        port=args.port,
        open_browser=open_browser
    )


def cmd_agent(args):
    """Run local agent to send data to remote server."""
    import uuid
    import time
    import requests
    import threading
    
    # Generate agent ID if not provided
    agent_id = args.agent_id or str(uuid.uuid4())[:8]
    
    # Initialize SES if not already done
    initialize(project_id=args.project_id)
    
    print("=" * 50)
    print("SES Intelligence - Remote Agent")
    print("=" * 50)
    print(f"🔗 Server: {args.server}")
    print(f"📦 Project: {args.project_id}")
    print(f"🆔 Agent ID: {agent_id}")
    print(f"📝 Agent Name: {args.agent_name}")
    print(f"⏱️  Heartbeat: every {args.interval} seconds")
    print("=" * 50)
    print("Press Ctrl+C to stop the agent\n")
    
    # Register with the remote server
    register_url = f"{args.server}/api/v1/agent/register/"
    try:
        response = requests.post(
            register_url,
            json={
                "agent_id": agent_id,
                "agent_name": args.agent_name,
                "project_id": args.project_id
            },
            timeout=10
        )
        if response.status_code == 200:
            print(f"✅ Registered with remote server")
        else:
            print(f"⚠️  Registration failed: {response.status_code}")
            print(f"   {response.text}")
    except Exception as e:
        print(f"❌ Failed to connect to server: {e}")
        return
    
    # Stop event for graceful shutdown
    stop_event = threading.Event()
    
    def send_heartbeat():
        """Send heartbeat to remote server."""
        heartbeat_url = f"{args.server}/api/v1/agent/heartbeat/"
        
        while not stop_event.is_set():
            try:
                # Get current health data
                snapshots = get_runtime_snapshots(project_id=args.project_id)
                edge_features = []
                
                # Get health data
                health_engine = ArchitectureHealthEngine(
                    snapshots=snapshots,
                    edge_features=edge_features,
                    project_id=args.project_id,
                )
                
                try:
                    health_data = health_engine.compute()
                except Exception as e:
                    health_data = {"error": str(e)}
                
                # Prepare payload
                payload = {
                    "agent_id": agent_id,
                    "health_data": health_data,
                    "snapshots": [
                        {
                            "snapshot_id": s.snapshot_id,
                            "node_count": s.graph.number_of_nodes(),
                            "edge_count": s.graph.number_of_edges()
                        }
                        for s in snapshots
                    ] if snapshots else [],
                    "graph_data": {
                        "node_count": snapshots[-1].graph.number_of_nodes() if snapshots else 0,
                        "edge_count": snapshots[-1].graph.number_of_edges() if snapshots else 0
                    }
                }
                
                # Send heartbeat
                response = requests.post(
                    heartbeat_url,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"💓 Heartbeat sent - Health: {health_data.get('overall_score', 'N/A')}")
                else:
                    print(f"⚠️  Heartbeat failed: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error sending heartbeat: {e}")
            
            # Wait for next interval
            stop_event.wait(args.interval)
        
        # Unregister when stopping
        try:
            unregister_url = f"{args.server}/api/v1/agent/unregister/"
            requests.post(unregister_url, json={"agent_id": agent_id}, timeout=5)
            print("👋 Unregistered from server")
        except:
            pass
    
    # Start heartbeat thread
    heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
    heartbeat_thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping agent...")
        stop_event.set()
        heartbeat_thread.join(timeout=5)
        print("✅ Agent stopped")


if __name__ == "__main__":
    main()
