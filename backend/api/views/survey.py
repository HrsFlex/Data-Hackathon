from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
import pandas as pd
import uuid
import os

from api.models import Survey, SurveyColumn
from api.serializers import SurveySerializer, SurveyUploadSerializer


class SurveyViewSet(viewsets.ModelViewSet):
    serializer_class = SurveySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Survey.objects.filter(uploaded_by=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        survey = self.get_object()
        try:
            if survey.file_type in ['csv']:
                df = pd.read_csv(survey.original_file.path, nrows=10)
            elif survey.file_type in ['xlsx', 'xls']:
                df = pd.read_excel(survey.original_file.path, nrows=10)
            else:
                return Response(
                    {'error': 'Unsupported file type'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            preview_data = {
                'columns': list(df.columns),
                'data': df.to_dict('records'),
                'total_rows': len(df),
                'sample_rows': min(10, len(df))
            }
            
            return Response(preview_data)
            
        except Exception as e:
            return Response(
                {'error': f'Error reading file: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        survey = self.get_object()
        try:
            if survey.file_type in ['csv']:
                df = pd.read_csv(survey.original_file.path)
            elif survey.file_type in ['xlsx', 'xls']:
                df = pd.read_excel(survey.original_file.path)
            else:
                return Response(
                    {'error': 'Unsupported file type'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            survey.total_rows = len(df)
            survey.total_columns = len(df.columns)
            survey.save()
            
            SurveyColumn.objects.filter(survey=survey).delete()
            
            for idx, column in enumerate(df.columns):
                col_data = df[column]
                
                if pd.api.types.is_numeric_dtype(col_data):
                    data_type = 'numeric'
                    min_val = float(col_data.min()) if not col_data.empty else None
                    max_val = float(col_data.max()) if not col_data.empty else None
                    mean_val = float(col_data.mean()) if not col_data.empty else None
                    std_val = float(col_data.std()) if not col_data.empty else None
                elif pd.api.types.is_datetime64_any_dtype(col_data):
                    data_type = 'date'
                    min_val = max_val = mean_val = std_val = None
                elif pd.api.types.is_bool_dtype(col_data):
                    data_type = 'boolean'
                    min_val = max_val = mean_val = std_val = None
                else:
                    data_type = 'categorical' if col_data.nunique() < len(col_data) * 0.5 else 'text'
                    min_val = max_val = mean_val = std_val = None
                
                SurveyColumn.objects.create(
                    survey=survey,
                    name=str(column),
                    original_name=str(column),
                    data_type=data_type,
                    missing_count=col_data.isnull().sum(),
                    unique_count=col_data.nunique(),
                    min_value=min_val,
                    max_value=max_val,
                    mean_value=mean_val,
                    std_value=std_val,
                    position=idx,
                    is_weight=(str(column).lower() == survey.weight_column.lower() if survey.weight_column else False)
                )
            
            return Response({'message': 'Survey analysis completed successfully'})
            
        except Exception as e:
            return Response(
                {'error': f'Error analyzing file: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SurveyUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SurveyUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            file = serializer.validated_data['file']
            file_extension = file.name.lower().split('.')[-1]
            
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = default_storage.save(f"surveys/original/{unique_filename}", file)
            
            survey = Survey.objects.create(
                name=serializer.validated_data['name'],
                description=serializer.validated_data.get('description', ''),
                survey_type=serializer.validated_data['survey_type'],
                uploaded_by=request.user,
                original_file=file_path,
                file_type=file_extension,
                file_size=file.size,
                has_weights=serializer.validated_data.get('has_weights', False),
                weight_column=serializer.validated_data.get('weight_column', '')
            )
            
            return Response(
                SurveySerializer(survey).data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {'error': f'Error uploading file: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )