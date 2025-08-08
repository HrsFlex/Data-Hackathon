from rest_framework import serializers
from api.models import Survey, SurveyColumn


class SurveyColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyColumn
        fields = [
            'id', 'name', 'original_name', 'data_type', 'is_required', 'is_weight',
            'missing_count', 'unique_count', 'min_value', 'max_value', 
            'mean_value', 'std_value', 'position'
        ]
        read_only_fields = ['id']


class SurveySerializer(serializers.ModelSerializer):
    columns = SurveyColumnSerializer(many=True, read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    
    class Meta:
        model = Survey
        fields = [
            'id', 'name', 'description', 'survey_type', 'uploaded_by', 'uploaded_by_name',
            'original_file', 'file_type', 'file_size', 'total_rows', 'total_columns',
            'has_weights', 'weight_column', 'created_at', 'updated_at', 'columns'
        ]
        read_only_fields = ['id', 'uploaded_by', 'file_size', 'total_rows', 'total_columns', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class SurveyUploadSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    survey_type = serializers.ChoiceField(choices=Survey.SURVEY_TYPES, default='other')
    file = serializers.FileField()
    has_weights = serializers.BooleanField(default=False)
    weight_column = serializers.CharField(required=False, allow_blank=True)
    
    def validate_file(self, value):
        allowed_extensions = ['.csv', '.xlsx', '.xls']
        file_extension = value.name.lower().split('.')[-1]
        
        if f'.{file_extension}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type '.{file_extension}' not supported. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        max_size = 100 * 1024 * 1024  # 100MB
        if value.size > max_size:
            raise serializers.ValidationError(f"File size exceeds {max_size / (1024*1024):.0f}MB limit")
        
        return value