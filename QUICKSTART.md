# Self-Evolving Software Intelligence - Quickstart Guide

## What is SES Intelligence?

Self-Evolving Software Intelligence (SES Intelligence) is a runtime intelligence platform that monitors, analyzes, and explains software behavior changes in real-time. It tracks function calls, builds architecture graphs, detects anomalies, and provides AI-powered explanations.

## Installation

```bash
pip install ses-intelligence
```

Or install from source:

```bash
git clone https://github.com/your-org/self-explaining-software.git
cd self-explaining-software
pip install -e .
```

## Quick Start

### 1. Instrument Your Code

Use the `@trace_behavior` decorator to automatically monitor function calls:

```python
from ses_intelligence import trace_behavior

@trace_behavior
def process_order(order_id):
    # Your business logic
    result = validate_order(order_id)
    if result:
        return charge_customer(order_id)
    return False

@trace_behavior
def validate_order(order_id):
    # Validation logic
    return True

@trace_behavior
def charge_customer(order_id):
    # Payment processing
    return True
```

### 2. Run Your Application

Execute your instrumented code normally. SES Intelligence automatically:

- Tracks function call patterns
- Builds a runtime architecture graph
- Records execution metrics (call counts, durations)

### 3. View Intelligence Dashboard

Start the Django server and dashboard:

```bash
# Start Django backend
python manage.py runserver

# In another terminal, start the frontend
cd ses-dashboard
npm install
npm run dev
```

Open http://localhost:5173 to view the dashboard.

## Advanced Usage

### Multi-Project Isolation

```python
from ses_intelligence import ProjectStorage, get_project_storage

# Create a new project
project_id = "my-microservice"
storage = ProjectStorage(project_id)

# Or get existing project storage
storage = get_project_storage("my-microservice")
```

### Get Runtime Snapshots

```python
from ses_intelligence import get_runtime_snapshots, reset_runtime_state

# Get current runtime snapshots for analysis
snapshots = get_runtime_snapshots(project_id="default")

# Reset runtime state between requests
reset_runtime_state()
```

### Manual Edge Features

```python
from ses_intelligence import get_edge_features

# Get edge-level features for ML processing
features = get_edge_features()
# Returns: { (caller, callee): { call_count, avg_duration, ... } }
```

## API Endpoints

After starting the server, these endpoints are available:

| Endpoint                           | Description                       |
| ---------------------------------- | --------------------------------- |
| `GET /api/health/?project=<id>`    | Current architecture health score |
| `GET /api/forecast/?project=<id>`  | Predictive health forecast        |
| `GET /api/graph/?project=<id>`     | Runtime architecture graph        |
| `GET /api/executive/?project=<id>` | Executive summary                 |
| `GET /api/projects/`               | List all projects                 |

## Configuration

### Environment Variables

| Variable         | Description             | Default           |
| ---------------- | ----------------------- | ----------------- |
| `SES_PROJECT_ID` | Default project ID      | `"default"`       |
| `SES_DATA_DIR`   | Behavior data directory | `./behavior_data` |

### Django Middleware

Add the SES middleware to `settings.py`:

```python
MIDDLEWARE = [
    # ...
    'ses_intelligence.middleware.SESMiddleware',
]
```

## Understanding the Dashboard

### Health Gauge

- **Score (0-100)**: Overall architecture health
- **Trend**: Improving, stable, or degrading
- **Confidence**: How reliable the score is

### Architecture Graph

- **Nodes**: Functions/modules
- **Edges**: Call relationships
- **Stability Index**: How consistent the call pattern is
- **Anomaly Flag**: Potential issues detected

### Forecast Timeline

- **Historical**: Past health scores
- **Predicted**: Future trajectory with confidence intervals
- **Risk Level**: Predicted degradation severity

## Troubleshooting

### No Data Showing

1. Ensure your functions are decorated with `@trace_behavior`
2. Check that middleware is properly configured
3. Verify the project ID matches

### Low Confidence Score

- More data points improve confidence
- Run the application for longer periods
- Ensure consistent traffic patterns

### Questions?

- Check the full documentation at `/docs`
- Review API responses in browser developer tools
- Examine behavior data in `behavior_data/<project_id>/`
