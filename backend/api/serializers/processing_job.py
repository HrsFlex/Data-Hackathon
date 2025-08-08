from rest_framework import serializers
from api.models import ProcessingJob, ProcessingStep


class ProcessingStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingStep
        fields = [
            'id', 'name', 'step_type', 'description', 'status', 'order',
            'started_at', 'completed_at', 'error_message', 'results', 'logs'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at']


class ProcessingJobSerializer(serializers.ModelSerializer):
    steps = ProcessingStepSerializer(many=True, read_only=True)
    survey_name = serializers.CharField(source='survey.name', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcessingJob
        fields = [
            'id', 'survey', 'survey_name', 'user', 'user_name', 'status',
            'configuration', 'progress_percentage', 'started_at', 'completed_at',
            'error_message', 'processed_file', 'results_summary',
            'created_at', 'updated_at', 'steps', 'duration'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'progress_percentage', 'started_at',
            'completed_at', 'error_message', 'processed_file', 'results_summary',
            'created_at', 'updated_at', 'duration'
        ]

    def get_duration(self, obj):
        duration = obj.duration
        return duration.total_seconds() if duration else None

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ProcessingJobCreateSerializer(serializers.Serializer):
    survey_id = serializers.UUIDField()
    configuration = serializers.JSONField()
    
    def validate_configuration(self, value):
        required_fields = ['cleaning_steps', 'imputation_method', 'outlier_detection']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing required configuration field: {field}")
        return value