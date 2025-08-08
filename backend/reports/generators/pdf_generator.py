from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.graphics.shapes import Drawing, Line
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
from django.conf import settings
from django.core.files.base import ContentFile
import io
import os
import tempfile
import base64
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """
    Generate comprehensive PDF reports for survey data processing results.
    """
    
    def __init__(self, template_config=None):
        self.styles = getSampleStyleSheet()
        self.template_config = template_config or {}
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles for the report."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            textColor=colors.HexColor('#1565C0'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#1976D2'),
            spaceBefore=15,
            spaceAfter=10,
            leftIndent=0
        ))
        
        # Subsection header style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#424242'),
            spaceBefore=10,
            spaceAfter=8
        ))
        
        # Government header style
        self.styles.add(ParagraphStyle(
            name='GovHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))
    
    def generate_report(self, processing_job, report_data, output_path):
        """
        Generate complete PDF report for a processing job.
        
        Args:
            processing_job: ProcessingJob instance
            report_data: Dictionary containing all processed results
            output_path: Path to save the PDF file
        """
        try:
            logger.info(f"Starting PDF report generation for job {processing_job.id}")
            
            # Create document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build story (content)
            story = []
            
            # Add header and title
            story.extend(self._add_header())
            story.extend(self._add_title(processing_job))
            
            # Add executive summary
            story.extend(self._add_executive_summary(processing_job, report_data))
            
            # Add data overview
            story.extend(self._add_data_overview(processing_job.survey, report_data))
            
            # Add processing summary
            story.extend(self._add_processing_summary(report_data))
            
            # Add statistical results
            story.extend(self._add_statistical_results(report_data))
            
            # Add data quality assessment
            story.extend(self._add_data_quality_assessment(report_data))
            
            # Add methodology section
            story.extend(self._add_methodology_section(processing_job))
            
            # Add appendix
            story.extend(self._add_appendix(report_data))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"PDF report generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise
    
    def _add_header(self):
        """Add government header to the report."""
        story = []
        
        # Government of India header
        header_text = """
        <para align="center">
            <b>GOVERNMENT OF INDIA</b><br/>
            MINISTRY OF STATISTICS AND PROGRAMME IMPLEMENTATION<br/>
            AI-Enhanced Survey Data Processing System
        </para>
        """
        
        story.append(Paragraph(header_text, self.styles['GovHeader']))
        story.append(Spacer(1, 20))
        
        # Add a horizontal line
        drawing = Drawing(400, 1)
        line = Line(0, 0, 400, 0)
        line.strokeColor = colors.HexColor('#1565C0')
        line.strokeWidth = 2
        drawing.add(line)
        story.append(drawing)
        story.append(Spacer(1, 20))
        
        return story
    
    def _add_title(self, processing_job):
        """Add report title section."""
        story = []
        
        # Main title
        title_text = f"Survey Data Processing Report<br/>{processing_job.survey.name}"
        story.append(Paragraph(title_text, self.styles['CustomTitle']))
        
        # Report metadata
        metadata_text = f"""
        <para align="center">
            Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
            Survey Type: {processing_job.survey.get_survey_type_display()}<br/>
            Processing Job ID: {str(processing_job.id)[:8]}
        </para>
        """
        
        story.append(Paragraph(metadata_text, self.styles['Normal']))
        story.append(Spacer(1, 30))
        
        return story
    
    def _add_executive_summary(self, processing_job, report_data):
        """Add executive summary section."""
        story = []
        
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        summary_text = f"""
        This report presents the results of automated survey data processing for {processing_job.survey.name}.
        The processing pipeline successfully completed {len([s for s in processing_job.steps.all() if s.status == 'completed'])} 
        out of {processing_job.steps.count()} processing steps.
        """
        
        if 'estimates' in report_data:
            estimates = report_data['estimates']
            if 'weighted' in estimates:
                weighted_count = len(estimates['weighted'])
                summary_text += f" A total of {weighted_count} statistical estimates were calculated with appropriate margins of error."
        
        if 'data_quality' in report_data:
            quality = report_data['data_quality']
            missing_pct = quality.get('missing_percentage', 0)
            summary_text += f" Data quality assessment shows {missing_pct:.1f}% missing values were successfully handled."
        
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        return story
    
    def _add_data_overview(self, survey, report_data):
        """Add data overview section."""
        story = []
        
        story.append(Paragraph("Data Overview", self.styles['SectionHeader']))
        
        # Basic dataset information
        data_info = [
            ['Dataset Name', survey.name],
            ['Survey Type', survey.get_survey_type_display()],
            ['File Format', survey.file_type.upper()],
            ['Total Records', f"{survey.total_rows:,}" if survey.total_rows else 'N/A'],
            ['Total Variables', f"{survey.total_columns:,}" if survey.total_columns else 'N/A'],
            ['Has Survey Weights', 'Yes' if survey.has_weights else 'No'],
            ['Upload Date', survey.created_at.strftime('%B %d, %Y')]
        ]
        
        table = Table(data_info, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E3F2FD')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BBBBBB'))
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _add_processing_summary(self, report_data):
        """Add processing summary section."""
        story = []
        
        story.append(Paragraph("Processing Summary", self.styles['SectionHeader']))
        
        processing_sections = [
            ('Data Cleaning', 'imputation'),
            ('Outlier Detection', 'outliers'),
            ('Data Validation', 'validation'),
            ('Weight Application', 'weights')
        ]
        
        for section_name, data_key in processing_sections:
            if data_key in report_data:
                story.append(Paragraph(section_name, self.styles['SubsectionHeader']))
                
                section_data = report_data[data_key]
                
                if data_key == 'imputation' and 'columns_processed' in section_data:
                    imputation_table = []
                    imputation_table.append(['Column', 'Method', 'Missing Values', 'Imputed Count'])
                    
                    for col_info in section_data['columns_processed'][:10]:  # Limit to first 10
                        imputation_table.append([
                            col_info.get('column', 'N/A'),
                            col_info.get('method', 'N/A'),
                            str(col_info.get('missing_count', 0)),
                            str(col_info.get('imputed_count', 0))
                        ])
                    
                    if len(imputation_table) > 1:
                        table = Table(imputation_table, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch])
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        story.append(table)
                
                elif data_key == 'outliers' and 'columns_processed' in section_data:
                    outlier_summary = f"""
                    Total outliers detected: {section_data.get('total_outliers_detected', 0)}<br/>
                    Columns processed: {len(section_data.get('columns_processed', []))}
                    """
                    story.append(Paragraph(outlier_summary, self.styles['Normal']))
                
                elif data_key == 'validation' and 'rules_applied' in section_data:
                    validation_summary = f"""
                    Validation rules applied: {len(section_data.get('rules_applied', []))}<br/>
                    Total violations found: {section_data.get('total_violations', 0)}
                    """
                    story.append(Paragraph(validation_summary, self.styles['Normal']))
                
                story.append(Spacer(1, 15))
        
        return story
    
    def _add_statistical_results(self, report_data):
        """Add statistical results section."""
        story = []
        
        if 'estimates' not in report_data:
            return story
        
        story.append(Paragraph("Statistical Results", self.styles['SectionHeader']))
        
        estimates = report_data['estimates']
        
        # Weighted estimates table
        if 'weighted' in estimates and estimates['weighted']:
            story.append(Paragraph("Weighted Estimates", self.styles['SubsectionHeader']))
            
            results_table = []
            results_table.append(['Variable', 'Estimate', 'Standard Error', 'Margin of Error', 'Confidence Interval'])
            
            for var_name, result in list(estimates['weighted'].items())[:10]:  # Limit to first 10
                if isinstance(result, dict):
                    ci_text = f"({result.get('confidence_interval', ['N/A', 'N/A'])[0]:.3f}, {result.get('confidence_interval', ['N/A', 'N/A'])[1]:.3f})" if 'confidence_interval' in result else 'N/A'
                    
                    results_table.append([
                        var_name,
                        f"{result.get('estimate', 0):.4f}",
                        f"{result.get('standard_error', 0):.4f}",
                        f"{result.get('margin_of_error', 0):.4f}",
                        ci_text
                    ])
            
            if len(results_table) > 1:
                table = Table(results_table, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1.5*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 15))
        
        # Weight effectiveness summary
        if 'weight_effectiveness' in estimates:
            effectiveness = estimates['weight_effectiveness']
            story.append(Paragraph("Weight Effectiveness Assessment", self.styles['SubsectionHeader']))
            
            effectiveness_text = f"""
            Coefficient of Variation: {effectiveness.get('coefficient_of_variation', 0):.3f}<br/>
            Effective Sample Size Ratio: {effectiveness.get('effective_sample_size_ratio', 0):.3f}<br/>
            Assessment: {effectiveness.get('assessment', 'Not available')}
            """
            story.append(Paragraph(effectiveness_text, self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        return story
    
    def _add_data_quality_assessment(self, report_data):
        """Add data quality assessment section."""
        story = []
        
        story.append(Paragraph("Data Quality Assessment", self.styles['SectionHeader']))
        
        if 'data_quality' in report_data:
            quality = report_data['data_quality']
            
            quality_metrics = [
                ['Metric', 'Value'],
                ['Completeness Rate', f"{100 - quality.get('missing_percentage', 0):.1f}%"],
                ['Data Consistency', quality.get('consistency_score', 'Good')],
                ['Outlier Rate', f"{quality.get('outlier_percentage', 0):.2f}%"],
                ['Validation Pass Rate', f"{quality.get('validation_pass_rate', 100):.1f}%"]
            ]
            
            table = Table(quality_metrics, colWidths=[2*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
        else:
            story.append(Paragraph("Data quality assessment not available.", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
        return story
    
    def _add_methodology_section(self, processing_job):
        """Add methodology section."""
        story = []
        
        story.append(Paragraph("Methodology", self.styles['SectionHeader']))
        
        # Processing steps methodology
        story.append(Paragraph("Processing Steps Applied", self.styles['SubsectionHeader']))
        
        steps_table = []
        steps_table.append(['Step', 'Method', 'Status'])
        
        for step in processing_job.steps.all():
            steps_table.append([
                step.name,
                step.get_step_type_display(),
                step.get_status_display()
            ])
        
        table = Table(steps_table, colWidths=[2*inch, 2*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Statistical methods
        methodology_text = """
        <b>Statistical Methods Used:</b><br/>
        • Missing Value Imputation: Mean, median, and K-Nearest Neighbors (KNN) methods<br/>
        • Outlier Detection: Interquartile Range (IQR), Z-score, and Modified Z-score methods<br/>
        • Survey Weight Application: Design weights applied with proper variance estimation<br/>
        • Confidence Intervals: Calculated using appropriate degrees of freedom and t-distribution<br/>
        • Data Validation: Rule-based consistency checks and skip-pattern validation<br/><br/>
        
        <b>Quality Assurance:</b><br/>
        • All statistical calculations follow established methodological standards<br/>
        • Results are reproducible and fully documented<br/>
        • Processing workflow maintains complete audit trail<br/>
        """
        
        story.append(Paragraph(methodology_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        return story
    
    def _add_appendix(self, report_data):
        """Add appendix section."""
        story = []
        
        story.append(PageBreak())
        story.append(Paragraph("Appendix", self.styles['SectionHeader']))
        
        # Processing logs
        if 'processing_logs' in report_data:
            story.append(Paragraph("Processing Logs", self.styles['SubsectionHeader']))
            
            logs = report_data['processing_logs'][:20]  # Limit to first 20 log entries
            for log_entry in logs:
                log_text = f"[{log_entry.get('timestamp', 'N/A')}] {log_entry.get('message', 'N/A')}"
                story.append(Paragraph(log_text, self.styles['Code']))
            
            story.append(Spacer(1, 20))
        
        # Technical specifications
        story.append(Paragraph("Technical Specifications", self.styles['SubsectionHeader']))
        
        tech_specs = """
        <b>System Information:</b><br/>
        • Application: AI-Enhanced Survey Data Processing System<br/>
        • Version: 1.0.0<br/>
        • Processing Engine: Python with pandas, numpy, scipy<br/>
        • Statistical Libraries: scikit-learn, statsmodels<br/>
        • Report Generation: ReportLab PDF Engine<br/><br/>
        
        <b>Data Security:</b><br/>
        • All data processed in secure environment<br/>
        • No personal information exposed in reports<br/>
        • Processing logs maintained for audit purposes<br/>
        """
        
        story.append(Paragraph(tech_specs, self.styles['Normal']))
        
        return story
    
    def embed_chart_image(self, chart_base64, width=4*inch, height=3*inch):
        """
        Embed a base64 chart image in the PDF.
        
        Args:
            chart_base64: Base64 encoded image string
            width: Image width
            height: Image height
        """
        try:
            # Decode base64 image
            if chart_base64.startswith('data:image/png;base64,'):
                image_data = base64.b64decode(chart_base64.split(',')[1])
            else:
                image_data = base64.b64decode(chart_base64)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                temp_file.write(image_data)
                temp_file_path = temp_file.name
            
            # Create ReportLab image
            img = Image(temp_file_path, width=width, height=height)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return img
        
        except Exception as e:
            logger.error(f"Error embedding chart image: {str(e)}")
            # Return placeholder text if image fails
            return Paragraph("Chart could not be displayed", self.styles['Normal'])