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


if __name__ == "__main__":
    main()
