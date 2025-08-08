from django.db import models
from django.contrib.auth.models import User
from .survey import Survey
import uuid
import json


class ProcessingJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='processing_jobs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='processing_jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    configuration = models.JSONField(default=dict)
    progress_percentage = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    processed_file = models.FileField(upload_to='surveys/processed/', blank=True)
    results_summary = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Job {self.id} - {self.survey.name} ({self.status})"

    @property
    def duration(self):
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    def add_step(self, name, description="", status="pending"):
        return ProcessingStep.objects.create(
            job=self,
            name=name,
            description=description,
            status=status,
            order=self.steps.count() + 1
        )


class ProcessingStep(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]

    STEP_TYPES = [
        ('upload', 'File Upload'),
        ('validation', 'Data Validation'),
        ('cleaning', 'Data Cleaning'),
        ('imputation', 'Missing Value Imputation'),
        ('outlier_detection', 'Outlier Detection'),
        ('rule_validation', 'Rule-based Validation'),
        ('weight_application', 'Weight Application'),
        ('estimation', 'Statistical Estimation'),
        ('report_generation', 'Report Generation'),
    ]

    job = models.ForeignKey(ProcessingJob, on_delete=models.CASCADE, related_name='steps')
    name = models.CharField(max_length=255)
    step_type = models.CharField(max_length=30, choices=STEP_TYPES, default='validation')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order = models.PositiveIntegerField()
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    results = models.JSONField(default=dict)
    logs = models.TextField(blank=True)

    class Meta:
        ordering = ['order']
        unique_together = ['job', 'order']

    def __str__(self):
        return f"{self.job.id} - Step {self.order}: {self.name}"