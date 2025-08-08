from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from api.models import ProcessingJob, Survey
from api.serializers import ProcessingJobSerializer, ProcessingJobCreateSerializer


class ProcessingJobViewSet(viewsets.ModelViewSet):
    serializer_class = ProcessingJobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProcessingJob.objects.filter(user=self.request.user).order_by('-created_at')

    def create(self, request):
        serializer = ProcessingJobCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        survey_id = serializer.validated_data['survey_id']
        survey = get_object_or_404(Survey, id=survey_id, uploaded_by=request.user)
        
        try:
            job = ProcessingJob.objects.create(
                survey=survey,
                user=request.user,
                configuration=serializer.validated_data['configuration']
            )
            
            job.add_step('Data Validation', 'Validate uploaded data format and integrity')
            job.add_step('Data Cleaning', 'Apply cleaning algorithms based on configuration')
            job.add_step('Missing Value Imputation', 'Handle missing values using specified method')
            job.add_step('Outlier Detection', 'Identify and handle outliers')
            job.add_step('Rule-based Validation', 'Apply consistency checks and skip patterns')
            job.add_step('Weight Application', 'Apply design weights if specified')
            job.add_step('Statistical Estimation', 'Calculate population parameters and margins of error')
            job.add_step('Report Generation', 'Generate final PDF/HTML report')
            
            # Here we would typically trigger a Celery task to process the job
            # For now, we'll just return the created job
            
            return Response(
                ProcessingJobSerializer(job).data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {'error': f'Error creating processing job: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        job = self.get_object()
        
        if job.status != 'pending':
            return Response(
                {'error': 'Job is not in pending status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            job.status = 'running'
            job.save()
            
            # Here we would trigger the actual processing pipeline
            # For now, we'll just update the status
            
            return Response({'message': 'Job started successfully'})
            
        except Exception as e:
            return Response(
                {'error': f'Error starting job: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        job = self.get_object()
        
        if job.status not in ['pending', 'running']:
            return Response(
                {'error': 'Job cannot be cancelled in current status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            job.status = 'cancelled'
            job.save()
            
            return Response({'message': 'Job cancelled successfully'})
            
        except Exception as e:
            return Response(
                {'error': f'Error cancelling job: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        job = self.get_object()
        
        progress_data = {
            'job_id': job.id,
            'status': job.status,
            'progress_percentage': job.progress_percentage,
            'current_step': None,
            'completed_steps': 0,
            'total_steps': job.steps.count(),
            'error_message': job.error_message
        }
        
        running_step = job.steps.filter(status='running').first()
        if running_step:
            progress_data['current_step'] = {
                'name': running_step.name,
                'description': running_step.description,
                'started_at': running_step.started_at
            }
        
        progress_data['completed_steps'] = job.steps.filter(status='completed').count()
        
        return Response(progress_data)