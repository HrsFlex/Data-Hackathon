from django.db import models
from django.contrib.auth.models import User
import uuid


class Survey(models.Model):
    SURVEY_TYPES = [
        ('household', 'Household Survey'),
        ('enterprise', 'Enterprise Survey'),
        ('agriculture', 'Agriculture Survey'),
        ('consumption', 'Consumption Expenditure Survey'),
        ('employment', 'Employment Survey'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    survey_type = models.CharField(max_length=20, choices=SURVEY_TYPES, default='other')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='surveys')
    original_file = models.FileField(upload_to='surveys/original/')
    file_type = models.CharField(max_length=10)
    file_size = models.PositiveIntegerField()
    total_rows = models.PositiveIntegerField(null=True, blank=True)
    total_columns = models.PositiveIntegerField(null=True, blank=True)
    has_weights = models.BooleanField(default=False)
    weight_column = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.survey_type})"


class SurveyColumn(models.Model):
    DATA_TYPES = [
        ('numeric', 'Numeric'),
        ('categorical', 'Categorical'),
        ('text', 'Text'),
        ('date', 'Date'),
        ('boolean', 'Boolean'),
    ]

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255)
    data_type = models.CharField(max_length=20, choices=DATA_TYPES)
    is_required = models.BooleanField(default=False)
    is_weight = models.BooleanField(default=False)
    missing_count = models.PositiveIntegerField(default=0)
    unique_count = models.PositiveIntegerField(default=0)
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    mean_value = models.FloatField(null=True, blank=True)
    std_value = models.FloatField(null=True, blank=True)
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ['position']
        unique_together = ['survey', 'position']

    def __str__(self):
        return f"{self.survey.name} - {self.name}"