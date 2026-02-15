import uuid
import json
from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    """
    Represents a project tracked by the Self-Evolving Software engine.
    
    Provides:
    - Ownership via User association
    - Project identification
    - Metadata storage
    """
    
    id = models.CharField(
        max_length=64,
        primary_key=True,
        editable=False,
        help_text="Unique project identifier (auto-generated)"
    )
    
    name = models.CharField(
        max_length=255,
        help_text="Human-readable project name"
    )
    
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ses_projects',
        help_text="User who owns this project"
    )
    
    description = models.TextField(
        blank=True,
        default='',
        help_text="Optional project description"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the project was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last time the project was updated"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this project is actively being tracked"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
    
    def __str__(self):
        return f"{self.name} ({self.id})"
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)
    
    @property
    def snapshot_count(self):
        """Get the number of snapshots for this project."""
        return self.snapshots.count()
    
    @property
    def latest_health_score(self):
        """Get the most recent health score."""
        latest_health = self.health_records.first()
        return latest_health.health_score if latest_health else None


class Snapshot(models.Model):
    """
    Represents a behavior snapshot captured at a point in time.
    
    Stores the raw call graph data for the project at a specific timestamp.
    This enables:
    - Queryable history
    - Audit trails
    - Forensic analysis
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique snapshot identifier"
    )
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='snapshots',
        help_text="Project this snapshot belongs to"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When this snapshot was captured"
    )
    
    node_count = models.IntegerField(
        default=0,
        help_text="Number of nodes in the call graph"
    )
    
    edge_count = models.IntegerField(
        default=0,
        help_text="Number of edges in the call graph"
    )
    
    raw_data = models.JSONField(
        default=dict,
        help_text="Raw snapshot data (call graph, metrics, etc.)"
    )
    
    edge_signature = models.JSONField(
        default=dict,
        help_text="Edge signature for change detection"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Snapshot'
        verbose_name_plural = 'Snapshots'
        indexes = [
            models.Index(fields=['project', '-timestamp']),
        ]
    
    def __str__(self):
        return f"Snapshot {self.id} for {self.project.name} at {self.timestamp}"


class HealthRecord(models.Model):
    """
    Represents an architecture health assessment record.
    
    Stores computed health metrics for each assessment, enabling:
    - Historical trending
    - Queryable health data
    - Performance analytics
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique health record identifier"
    )
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='health_records',
        help_text="Project this health record belongs to"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When this health assessment was computed"
    )
    
    health_score = models.FloatField(
        help_text="Overall health score (0.0 - 1.0)"
    )
    
    # Component scores
    stability_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Stability component score"
    )
    
    complexity_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Complexity component score"
    )
    
    coupling_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Coupling component score"
    )
    
    # Risk indicators
    risk_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='low',
        help_text="Current risk level"
    )
    
    risk_indicators = models.JSONField(
        default=list,
        help_text="List of active risk indicators"
    )
    
    # Raw output for detailed analysis
    raw_output = models.JSONField(
        default=dict,
        help_text="Full health computation output"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Health Record'
        verbose_name_plural = 'Health Records'
        indexes = [
            models.Index(fields=['project', '-timestamp']),
            models.Index(fields=['project', '-health_score']),
        ]
    
    def __str__(self):
        return f"Health {self.health_score} for {self.project.name} at {self.timestamp}"


class ForecastRecord(models.Model):
    """
    Represents a forecast prediction record.
    
    Stores forecast computations and confidence metrics, enabling:
    - Forecast accuracy analysis
    - Trend visualization
    - Confidence tracking over time
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique forecast record identifier"
    )
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='forecast_records',
        help_text="Project this forecast belongs to"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When this forecast was computed"
    )
    
    # Forecast values
    forecast_next = models.FloatField(
        help_text="Predicted next health score"
    )
    
    forecast_window = models.IntegerField(
        default=10,
        help_text="Window size used for forecasting"
    )
    
    # Confidence metrics
    confidence_score = models.FloatField(
        help_text="Confidence score (0.0 - 1.0)"
    )
    
    confidence_interval_lower = models.FloatField(
        null=True,
        blank=True,
        help_text="Lower bound of confidence interval"
    )
    
    confidence_interval_upper = models.FloatField(
        null=True,
        blank=True,
        help_text="Upper bound of confidence interval"
    )
    
    # Error metrics
    rmse = models.FloatField(
        null=True,
        blank=True,
        help_text="Root mean square error"
    )
    
    residual_variance = models.FloatField(
        null=True,
        blank=True,
        help_text="Variance of residuals"
    )
    
    # Volatility
    volatility = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('moderate', 'Moderate'),
            ('high', 'High'),
        ],
        default='low',
        help_text="Volatility classification"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('insufficient_data', 'Insufficient Data'),
            ('error', 'Error'),
        ],
        default='success',
        help_text="Forecast computation status"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Forecast Record'
        verbose_name_plural = 'Forecast Records'
        indexes = [
            models.Index(fields=['project', '-timestamp']),
        ]
    
    def __str__(self):
        return f"Forecast {self.forecast_next} for {self.project.name} at {self.timestamp}"
