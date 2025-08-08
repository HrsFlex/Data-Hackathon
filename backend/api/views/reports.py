from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponse
from django.core.files.base import ContentFile
from django.conf import settings
import os
import tempfile
import uuid
from datetime import datetime
import logging

from api.models import ProcessingJob, Survey
from reports.models import GeneratedReport, ReportTemplate
from reports.generators import PDFReportGenerator, HTMLReportGenerator, VisualizationEngine
from data_processing.algorithms import ImputationEngine, OutlierDetectionEngine, RuleValidationEngine, WeightApplicationEngine

logger = logging.getLogger(__name__)


class ReportGenerationView(APIView):
    """Generate reports for completed processing jobs."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Generate a new report for a processing job.
        
        Expected payload:
        {
            "job_id": "uuid-string",
            "format": "pdf" or "html",
            "template_id": "optional-template-uuid",
            "include_charts": true/false
        }
        """
        try:
            job_id = request.data.get('job_id')
            format_type = request.data.get('format', 'pdf')
            template_id = request.data.get('template_id')
            include_charts = request.data.get('include_charts', True)
            
            if not job_id:
                return Response(
                    {'error': 'job_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get processing job
            job = get_object_or_404(ProcessingJob, id=job_id, user=request.user)
            
            if job.status != 'completed':
                return Response(
                    {'error': 'Can only generate reports for completed jobs'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create report template
            template = None
            if template_id:
                template = get_object_or_404(ReportTemplate, id=template_id)
            
            # Create report record
            report = GeneratedReport.objects.create(
                processing_job=job,
                template=template,
                format=format_type,
                title=f"{job.survey.name} - Processing Report",
                generated_by=request.user,
                generation_config={
                    'include_charts': include_charts,
                    'format': format_type,
                    'template_id': str(template_id) if template_id else None
                }
            )
            
            # Generate report data
            report_data = self._prepare_report_data(job, include_charts)
            report.report_data = report_data
            
            # Generate report file
            generation_start = datetime.now()
            
            if format_type == 'pdf':
                file_path = self._generate_pdf_report(job, report_data, report.id)
            elif format_type == 'html':
                file_path = self._generate_html_report(job, report_data, report.id)
            else:
                return Response(
                    {'error': 'Unsupported format. Use "pdf" or "html"'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            generation_time = (datetime.now() - generation_start).total_seconds()
            
            # Update report record
            with open(file_path, 'rb') as f:
                file_content = ContentFile(f.read())
                report.report_file.save(
                    f"report_{report.id}.{format_type}",
                    file_content
                )
            
            report.status = 'completed'
            report.generation_time_seconds = generation_time
            report.file_size = os.path.getsize(file_path)
            report.save()
            
            # Clean up temporary file
            os.unlink(file_path)
            
            return Response({
                'report_id': report.id,
                'status': 'completed',
                'format': format_type,
                'file_size': report.file_size,
                'generation_time': generation_time,
                'download_url': f'/api/v1/reports/{report.id}/download/'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            
            # Update report status to failed if it exists
            if 'report' in locals():
                report.status = 'failed'
                report.error_message = str(e)
                report.save()
            
            return Response(
                {'error': f'Report generation failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _prepare_report_data(self, job, include_charts=True):
        """Prepare comprehensive report data from processing job."""
        report_data = {
            'job_metadata': {
                'id': str(job.id),
                'status': job.status,
                'created_at': job.created_at.isoformat(),
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'progress_percentage': job.progress_percentage,
                'configuration': job.configuration
            },
            'survey_metadata': {
                'name': job.survey.name,
                'description': job.survey.description,
                'survey_type': job.survey.survey_type,
                'total_rows': job.survey.total_rows,
                'total_columns': job.survey.total_columns,
                'has_weights': job.survey.has_weights,
                'weight_column': job.survey.weight_column,
                'file_type': job.survey.file_type
            }
        }
        
        # Add processing steps information
        steps_data = []
        for step in job.steps.all():
            steps_data.append({
                'name': step.name,
                'step_type': step.step_type,
                'status': step.status,
                'started_at': step.started_at.isoformat() if step.started_at else None,
                'completed_at': step.completed_at.isoformat() if step.completed_at else None,
                'error_message': step.error_message,
                'results': step.results
            })
        report_data['processing_steps'] = steps_data
        
        # Extract results from job's results_summary
        if job.results_summary:
            # Add statistical estimates
            if 'estimates' in job.results_summary:
                report_data['estimates'] = job.results_summary['estimates']
            
            # Add data processing summaries
            for key in ['imputation', 'outliers', 'validation', 'weights']:
                if key in job.results_summary:
                    report_data[key] = job.results_summary[key]
        
        # Generate data quality assessment
        report_data['data_quality'] = self._assess_data_quality(job)
        
        # Generate charts if requested
        if include_charts:
            report_data['charts'] = self._generate_charts(job, report_data)
        
        # Add processing logs
        report_data['processing_logs'] = self._extract_processing_logs(job)
        
        return report_data
    
    def _assess_data_quality(self, job):
        """Assess overall data quality from processing results."""
        quality_assessment = {
            'overall_score': 'Good',
            'missing_percentage': 0,
            'outlier_percentage': 0,
            'consistency_score': 'Good',
            'validation_pass_rate': 100
        }
        
        # Extract quality metrics from job results
        if job.results_summary:
            if 'imputation' in job.results_summary:
                imp_data = job.results_summary['imputation']
                total_before = imp_data.get('total_missing_before', 0)
                total_records = job.survey.total_rows or 1
                quality_assessment['missing_percentage'] = (total_before / total_records) * 100
            
            if 'outliers' in job.results_summary:
                outlier_data = job.results_summary['outliers']
                total_outliers = outlier_data.get('total_outliers_detected', 0)
                total_records = job.survey.total_rows or 1
                quality_assessment['outlier_percentage'] = (total_outliers / total_records) * 100
            
            if 'validation' in job.results_summary:
                val_data = job.results_summary['validation']
                total_violations = val_data.get('total_violations', 0)
                total_records = job.survey.total_rows or 1
                pass_rate = max(0, 100 - (total_violations / total_records) * 100)
                quality_assessment['validation_pass_rate'] = pass_rate
        
        # Determine overall score
        scores = []
        if quality_assessment['missing_percentage'] < 5:
            scores.append(4)
        elif quality_assessment['missing_percentage'] < 15:
            scores.append(3)
        else:
            scores.append(2)
        
        if quality_assessment['outlier_percentage'] < 2:
            scores.append(4)
        elif quality_assessment['outlier_percentage'] < 5:
            scores.append(3)
        else:
            scores.append(2)
        
        if quality_assessment['validation_pass_rate'] > 95:
            scores.append(4)
        elif quality_assessment['validation_pass_rate'] > 85:
            scores.append(3)
        else:
            scores.append(2)
        
        avg_score = sum(scores) / len(scores)
        if avg_score >= 3.5:
            quality_assessment['overall_score'] = 'Excellent'
        elif avg_score >= 2.5:
            quality_assessment['overall_score'] = 'Good'
        else:
            quality_assessment['overall_score'] = 'Fair'
        
        return quality_assessment
    
    def _generate_charts(self, job, report_data):
        """Generate visualization charts for the report."""
        charts = {}
        
        try:
            viz_engine = VisualizationEngine()
            
            # Create processing summary chart
            processing_stats = {
                'imputation': report_data.get('imputation', {}),
                'outliers': report_data.get('outliers', {}),
                'validation': report_data.get('validation', {}),
                'total_records': job.survey.total_rows or 0
            }
            
            summary_chart = viz_engine.create_processing_summary_chart(processing_stats)
            if summary_chart:
                charts['processing_summary'] = summary_chart
            
            # Create statistical results charts if available
            if 'estimates' in report_data:
                estimates_chart = viz_engine.create_statistical_charts(
                    report_data['estimates'], 
                    'estimates_comparison'
                )
                if estimates_chart:
                    charts['estimates_comparison'] = estimates_chart
                
                ci_chart = viz_engine.create_statistical_charts(
                    report_data['estimates'], 
                    'confidence_intervals'
                )
                if ci_chart:
                    charts['confidence_intervals'] = ci_chart
            
        except Exception as e:
            logger.error(f"Error generating charts: {str(e)}")
            charts['error'] = f"Chart generation failed: {str(e)}"
        
        return charts
    
    def _extract_processing_logs(self, job):
        """Extract processing logs from job steps."""
        logs = []
        
        for step in job.steps.all():
            if step.logs:
                logs.append({
                    'timestamp': step.started_at.isoformat() if step.started_at else None,
                    'step': step.name,
                    'message': step.logs
                })
        
        return logs
    
    def _generate_pdf_report(self, job, report_data, report_id):
        """Generate PDF report file."""
        try:
            # Create temporary file
            temp_dir = tempfile.mkdtemp()
            output_path = os.path.join(temp_dir, f"report_{report_id}.pdf")
            
            # Generate PDF
            pdf_generator = PDFReportGenerator()
            pdf_generator.generate_report(job, report_data, output_path)
            
            return output_path
            
        except Exception as e:
            logger.error(f"PDF generation error: {str(e)}")
            raise
    
    def _generate_html_report(self, job, report_data, report_id):
        """Generate HTML report file."""
        try:
            # Create temporary file
            temp_dir = tempfile.mkdtemp()
            output_path = os.path.join(temp_dir, f"report_{report_id}.html")
            
            # Generate HTML
            html_generator = HTMLReportGenerator()
            html_generator.generate_report(job, report_data, output_path)
            
            return output_path
            
        except Exception as e:
            logger.error(f"HTML generation error: {str(e)}")
            raise


class ReportDownloadView(APIView):
    """Download generated reports."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, report_id):
        """Download a generated report file."""
        try:
            report = get_object_or_404(
                GeneratedReport, 
                id=report_id, 
                generated_by=request.user
            )
            
            if report.status != 'completed' or not report.report_file:
                return Response(
                    {'error': 'Report not available for download'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Determine content type
            content_type_map = {
                'pdf': 'application/pdf',
                'html': 'text/html'
            }
            content_type = content_type_map.get(report.format, 'application/octet-stream')
            
            # Create file response
            response = FileResponse(
                report.report_file.open('rb'),
                content_type=content_type
            )
            
            filename = f"{report.title}_{report.created_at.strftime('%Y%m%d')}.{report.format}"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error downloading report: {str(e)}")
            return Response(
                {'error': f'Download failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReportListView(APIView):
    """List generated reports for the authenticated user."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of user's generated reports."""
        reports = GeneratedReport.objects.filter(
            generated_by=request.user
        ).select_related('processing_job', 'processing_job__survey').order_by('-created_at')
        
        reports_data = []
        for report in reports:
            reports_data.append({
                'id': report.id,
                'title': report.title,
                'format': report.format,
                'status': report.status,
                'file_size': report.file_size,
                'created_at': report.created_at,
                'generation_time': report.generation_time_seconds,
                'survey_name': report.processing_job.survey.name,
                'job_id': report.processing_job.id,
                'download_url': f'/api/v1/reports/{report.id}/download/' if report.status == 'completed' else None
            })
        
        return Response({
            'count': len(reports_data),
            'reports': reports_data
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def report_templates_list(request):
    """List available report templates."""
    from django.db import models
    templates = ReportTemplate.objects.filter(
        models.Q(is_public=True) | models.Q(created_by=request.user)
    ).order_by('-created_at')
    
    templates_data = []
    for template in templates:
        templates_data.append({
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'template_type': template.template_type,
            'is_public': template.is_public,
            'created_by': template.created_by.username,
            'created_at': template.created_at
        })
    
    return Response({
        'count': len(templates_data),
        'templates': templates_data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_report(request):
    """Generate dashboard report with multiple surveys overview."""
    try:
        # Get user's surveys
        surveys = Survey.objects.filter(uploaded_by=request.user).order_by('-created_at')[:20]
        
        surveys_data = []
        for survey in surveys:
            surveys_data.append({
                'id': survey.id,
                'name': survey.name,
                'survey_type': survey.survey_type,
                'get_survey_type_display': survey.get_survey_type_display(),
                'total_rows': survey.total_rows,
                'total_columns': survey.total_columns,
                'has_weights': survey.has_weights,
                'created_at': survey.created_at,
                'status': 'completed' if survey.processing_jobs.filter(status='completed').exists() else 'pending'
            })
        
        # Generate HTML dashboard
        html_generator = HTMLReportGenerator()
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, f"dashboard_{uuid.uuid4()}.html")
        
        html_generator.generate_dashboard_report(surveys_data, output_path)
        
        # Return HTML content
        with open(output_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Clean up
        os.unlink(output_path)
        
        return HttpResponse(html_content, content_type='text/html')
        
    except Exception as e:
        logger.error(f"Error generating dashboard report: {str(e)}")
        return Response(
            {'error': f'Dashboard generation failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )