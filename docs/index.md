# SES Intelligence SDK Documentation

Welcome to the **SES Intelligence SDK** documentation - a runtime intelligence platform that monitors, analyzes, and explains software behavior changes in real-time.

## What is SES Intelligence?

SES Intelligence is a **framework-agnostic SDK** that provides:

- **Behavior Tracing**: Automatically capture function call graphs
- **Health Monitoring**: Real-time architecture health scoring
- **Forecasting**: Predict future health trends
- **Narratives**: LLM-powered explanations of system behavior

## Installation

```bash
# Core package (minimal dependencies)
pip install ses-intelligence

# With all features
pip install ses-intelligence[all]

# With specific features
pip install ses-intelligence[ml,llm]
```

## Quick Start

```python
from ses_intelligence import initialize, trace_behavior

# Initialize with your project
initialize(project_id="my-app")

# Instrument your functions
@trace_behavior
def save_user(user_data):
    # Your business logic
    return {"status": "success"}
```

## CLI Commands

```bash
# Initialize a project
ses init --project-id my-app

# Check status
ses status

# Take a snapshot
ses snapshot

# Check health
ses health

# Run forecasting
ses forecast --horizon 5
```

## Supported Frameworks

- ✅ Plain Python
- ✅ Flask
- ✅ FastAPI
- ✅ Django
- ✅ Background workers

## API Reference

### Configuration

| Function           | Description                        |
| ------------------ | ---------------------------------- |
| `initialize()`     | Initialize SES with project config |
| `get_config()`     | Get current configuration          |
| `is_initialized()` | Check if SES is initialized        |

### Tracing

| Function              | Description                       |
| --------------------- | --------------------------------- |
| `@trace_behavior`     | Decorator to trace function calls |
| `get_edge_features()` | Get edge features for ML          |

### Runtime State

| Function                  | Description               |
| ------------------------- | ------------------------- |
| `get_runtime_snapshots()` | Get all runtime snapshots |
| `reset_runtime_state()`   | Reset runtime state       |

### Storage

| Class            | Description                   |
| ---------------- | ----------------------------- |
| `ProjectStorage` | Manage project-scoped storage |

## Configuration Options

```python
initialize(
    project_id="my-app",           # Required: unique project ID
    project_name="My Application",  # Optional: human-readable name
    storage_path="/data/ses",       # Optional: custom storage path
    enable_forecasting=True,        # Enable health forecasting
    enable_narratives=True,        # Enable LLM narratives
    llm_api_key="sk-...",          # OpenAI API key for LLM features
)
```

## Examples

See the `examples/` directory for complete examples:

- `examples/plain_python/` - Plain Python script example

## License

MIT License - see LICENSE file for details.
