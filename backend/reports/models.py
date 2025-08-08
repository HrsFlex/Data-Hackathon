from django.db import models
from django.contrib.auth.models import User
from api.models import Survey, ProcessingJob
import uuid


class ReportTemplate(models.Model):
    TEMPLATE_TYPES = [
        ('standard', 'Standard Survey Report'),
        ('summary', 'Executive Summary'),
        ('detailed', 'Detailed Analysis'),
        ('diagnostic', 'Data Quality Diagnostic'),
        ('custom', 'Custom Template'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES, default='standard')
    template_content = models.JSONField(default=dict)  # Template structure and configuration
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_templates')
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.template_type})"


class GeneratedReport(models.Model):
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('html', 'HTML'),
        ('docx', 'Word Document'),
    ]

    STATUS_CHOICES = [
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    processing_job = models.ForeignKey(ProcessingJob, on_delete=models.CASCADE, related_name='reports')
    template = models.ForeignKey(ReportTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generating')
    
    # Report content and metadata
    title = models.CharField(max_length=500)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_reports')
    report_data = models.JSONField(default=dict)  # Processed results and statistics
    
    # File storage
    report_file = models.FileField(upload_to='reports/generated/', blank=True)
    file_size = models.PositiveIntegerField(default=0)
    
    # Generation metadata
    generation_config = models.JSONField(default=dict)
    generation_time_seconds = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report for {self.processing_job.survey.name} - {self.format.upper()}"


class ReportSection(models.Model):
    SECTION_TYPES = [
        ('executive_summary', 'Executive Summary'),
        ('data_overview', 'Data Overview'),
        ('quality_assessment', 'Data Quality Assessment'),
        ('cleaning_summary', 'Data Cleaning Summary'),
        ('statistical_results', 'Statistical Results'),
        ('visualizations', 'Charts and Visualizations'),
        ('methodology', 'Methodology'),
        ('appendix', 'Appendix'),
    ]

    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='sections')
    section_type = models.CharField(max_length=30, choices=SECTION_TYPES)
    title = models.CharField(max_length=255)
    content_config = models.JSONField(default=dict)  # Configuration for section content
    order = models.PositiveIntegerField()
    is_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        unique_together = ['template', 'order']

    def __str__(self):
        return f"{self.template.name} - {self.title}"