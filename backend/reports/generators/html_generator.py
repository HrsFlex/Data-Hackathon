from jinja2 import Environment, FileSystemLoader, select_autoescape
from django.conf import settings
import os
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """
    Generate responsive HTML reports for survey data processing results.
    """
    
    def __init__(self, template_dir=None):
        self.template_dir = template_dir or os.path.join(
            settings.BASE_DIR, 'reports', 'templates', 'html'
        )
        
        # Ensure template directory exists
        os.makedirs(self.template_dir, exist_ok=True)
        
        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['datetime'] = self.datetime_filter
        self.env.filters['percentage'] = self.percentage_filter
        self.env.filters['number'] = self.number_filter
        self.env.filters['currency'] = self.currency_filter
    
    def datetime_filter(self, value, format='%B %d, %Y at %I:%M %p'):
        """Format datetime values."""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                return value
        if hasattr(value, 'strftime'):
            return value.strftime(format)
        return str(value)
    
    def percentage_filter(self, value, decimals=1):
        """Format as percentage."""
        try:
            return f"{float(value):.{decimals}f}%"
        except (ValueError, TypeError):
            return str(value)
    
    def number_filter(self, value, decimals=2):
        """Format numbers with commas."""
        try:
            if decimals == 0:
                return f"{int(float(value)):,}"
            else:
                return f"{float(value):,.{decimals}f}"
        except (ValueError, TypeError):
            return str(value)
    
    def currency_filter(self, value, symbol='₹'):
        """Format as currency."""
        try:
            return f"{symbol}{float(value):,.2f}"
        except (ValueError, TypeError):
            return str(value)
    
    def generate_report(self, processing_job, report_data, output_path):
        """
        Generate complete HTML report for a processing job.
        
        Args:
            processing_job: ProcessingJob instance
            report_data: Dictionary containing all processed results
            output_path: Path to save the HTML file
        """
        try:
            logger.info(f"Starting HTML report generation for job {processing_job.id}")
            
            # Ensure template exists
            self.ensure_base_template()
            
            # Prepare template context
            context = {
                'job': processing_job,
                'survey': processing_job.survey,
                'report_data': report_data,
                'generation_time': datetime.now(),
                'job_steps': list(processing_job.steps.all()),
                'completed_steps': processing_job.steps.filter(status='completed'),
                'total_steps': processing_job.steps.count(),
                'completion_rate': (processing_job.steps.filter(status='completed').count() / 
                                  processing_job.steps.count() * 100) if processing_job.steps.count() > 0 else 0
            }
            
            # Add processed statistics
            context.update(self._prepare_statistics(report_data))
            
            # Render template
            template = self.env.get_template('survey_report.html')
            html_content = template.render(context)
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML report generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}")
            raise
    
    def _prepare_statistics(self, report_data):
        """Prepare statistics for template rendering."""
        stats = {
            'has_estimates': 'estimates' in report_data,
            'has_quality_data': 'data_quality' in report_data,
            'has_processing_summary': any(key in report_data for key in ['imputation', 'outliers', 'validation']),
            'weighted_estimates': [],
            'unweighted_estimates': [],
            'processing_summary': {},
            'quality_metrics': {}
        }
        
        # Process estimates
        if 'estimates' in report_data:
            estimates = report_data['estimates']
            
            if 'weighted' in estimates:
                for var_name, result in estimates['weighted'].items():
                    if isinstance(result, dict):
                        stats['weighted_estimates'].append({
                            'variable': var_name,
                            'estimate': result.get('estimate', 0),
                            'standard_error': result.get('standard_error', 0),
                            'margin_of_error': result.get('margin_of_error', 0),
                            'confidence_interval': result.get('confidence_interval', [0, 0]),
                            'sample_size': result.get('sample_size', 0)
                        })
            
            if 'unweighted' in estimates:
                for var_name, result in estimates['unweighted'].items():
                    if isinstance(result, dict):
                        stats['unweighted_estimates'].append({
                            'variable': var_name,
                            'estimate': result.get('estimate', 0),
                            'standard_error': result.get('standard_error', 0),
                            'margin_of_error': result.get('margin_of_error', 0),
                            'confidence_interval': result.get('confidence_interval', [0, 0]),
                            'sample_size': result.get('sample_size', 0)
                        })
        
        # Process data quality metrics
        if 'data_quality' in report_data:
            quality = report_data['data_quality']
            stats['quality_metrics'] = {
                'completeness_rate': 100 - quality.get('missing_percentage', 0),
                'outlier_rate': quality.get('outlier_percentage', 0),
                'consistency_score': quality.get('consistency_score', 'Good'),
                'validation_pass_rate': quality.get('validation_pass_rate', 100)
            }
        
        # Process processing summary
        for key in ['imputation', 'outliers', 'validation']:
            if key in report_data:
                stats['processing_summary'][key] = report_data[key]
        
        return stats
    
    def ensure_base_template(self):
        """Ensure the base HTML template exists."""
        template_path = os.path.join(self.template_dir, 'survey_report.html')
        
        if not os.path.exists(template_path):
            logger.info("Creating base HTML template")
            base_template = self.get_base_template_content()
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(base_template)
    
    def get_base_template_content(self):
        """Get the base HTML template content."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Survey Data Processing Report - {{ survey.name }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        
        .header {
            text-align: center;
            border-bottom: 3px solid #1565C0;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .gov-header {
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }
        
        .title {
            color: #1565C0;
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            font-size: 16px;
        }
        
        .section {
            margin-bottom: 30px;
        }
        
        .section-title {
            color: #1976D2;
            font-size: 20px;
            font-weight: bold;
            border-bottom: 2px solid #E3F2FD;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }
        
        .subsection-title {
            color: #424242;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
            margin-top: 20px;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .info-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
        }
        
        .info-card h4 {
            color: #1976D2;
            margin-bottom: 10px;
        }
        
        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        
        .stat-row:last-child {
            border-bottom: none;
        }
        
        .stat-label {
            font-weight: 500;
        }
        
        .stat-value {
            color: #1976D2;
            font-weight: bold;
        }
        
        .table-container {
            overflow-x: auto;
            margin: 15px 0;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background-color: #1976D2;
            color: white;
            font-weight: bold;
        }
        
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #45a049);
            transition: width 0.3s ease;
        }
        
        .status-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-completed {
            background: #C8E6C9;
            color: #2E7D32;
        }
        
        .status-running {
            background: #FFF3E0;
            color: #F57C00;
        }
        
        .status-failed {
            background: #FFCDD2;
            color: #C62828;
        }
        
        .status-pending {
            background: #E1F5FE;
            color: #0277BD;
        }
        
        .chart-container {
            text-align: center;
            margin: 20px 0;
        }
        
        .methodology {
            background: #f8f9fa;
            border-left: 4px solid #1976D2;
            padding: 20px;
            margin: 20px 0;
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 14px;
        }
        
        @media print {
            body { background-color: white; }
            .container { box-shadow: none; }
        }
        
        @media (max-width: 768px) {
            .info-grid {
                grid-template-columns: 1fr;
            }
            
            .table-container {
                font-size: 14px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header Section -->
        <div class="header">
            <div class="gov-header">
                <strong>GOVERNMENT OF INDIA</strong><br>
                MINISTRY OF STATISTICS AND PROGRAMME IMPLEMENTATION<br>
                AI-Enhanced Survey Data Processing System
            </div>
            <h1 class="title">Survey Data Processing Report</h1>
            <h2 class="subtitle">{{ survey.name }}</h2>
            <p>Generated: {{ generation_time | datetime }} | Job ID: {{ job.id | truncate(8) }}</p>
        </div>

        <!-- Executive Summary -->
        <div class="section">
            <h2 class="section-title">Executive Summary</h2>
            <div class="info-grid">
                <div class="info-card">
                    <h4>Processing Status</h4>
                    <div class="stat-row">
                        <span class="stat-label">Completion Rate</span>
                        <span class="stat-value">{{ completion_rate | number(0) }}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {{ completion_rate }}%"></div>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Steps Completed</span>
                        <span class="stat-value">{{ completed_steps | length }} / {{ total_steps }}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Job Status</span>
                        <span class="status-badge status-{{ job.status }}">{{ job.get_status_display }}</span>
                    </div>
                </div>
                
                <div class="info-card">
                    <h4>Dataset Information</h4>
                    <div class="stat-row">
                        <span class="stat-label">Survey Type</span>
                        <span class="stat-value">{{ survey.get_survey_type_display }}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Records</span>
                        <span class="stat-value">{{ survey.total_rows | number(0) }}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Variables</span>
                        <span class="stat-value">{{ survey.total_columns | number(0) }}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Has Weights</span>
                        <span class="stat-value">{{ 'Yes' if survey.has_weights else 'No' }}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Data Quality Assessment -->
        {% if has_quality_data %}
        <div class="section">
            <h2 class="section-title">Data Quality Assessment</h2>
            <div class="info-grid">
                <div class="info-card">
                    <h4>Quality Metrics</h4>
                    <div class="stat-row">
                        <span class="stat-label">Completeness Rate</span>
                        <span class="stat-value">{{ quality_metrics.completeness_rate | percentage }}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Outlier Rate</span>
                        <span class="stat-value">{{ quality_metrics.outlier_rate | percentage }}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Consistency Score</span>
                        <span class="stat-value">{{ quality_metrics.consistency_score }}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Validation Pass Rate</span>
                        <span class="stat-value">{{ quality_metrics.validation_pass_rate | percentage }}</span>
                    </div>
                </div>
            </div>
        </div>
        {% endif %}

        <!-- Statistical Results -->
        {% if has_estimates %}
        <div class="section">
            <h2 class="section-title">Statistical Results</h2>
            
            {% if weighted_estimates %}
            <h3 class="subsection-title">Weighted Estimates</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Variable</th>
                            <th>Estimate</th>
                            <th>Standard Error</th>
                            <th>Margin of Error</th>
                            <th>95% Confidence Interval</th>
                            <th>Sample Size</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for est in weighted_estimates[:10] %}
                        <tr>
                            <td>{{ est.variable }}</td>
                            <td>{{ est.estimate | number(4) }}</td>
                            <td>{{ est.standard_error | number(4) }}</td>
                            <td>{{ est.margin_of_error | number(4) }}</td>
                            <td>({{ est.confidence_interval[0] | number(3) }}, {{ est.confidence_interval[1] | number(3) }})</td>
                            <td>{{ est.sample_size | number(0) }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
        </div>
        {% endif %}

        <!-- Processing Summary -->
        {% if has_processing_summary %}
        <div class="section">
            <h2 class="section-title">Processing Summary</h2>
            
            {% if processing_summary.imputation %}
            <h3 class="subsection-title">Missing Value Imputation</h3>
            <div class="info-card">
                <div class="stat-row">
                    <span class="stat-label">Total Missing Values Before</span>
                    <span class="stat-value">{{ processing_summary.imputation.total_missing_before | number(0) }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Total Missing Values After</span>
                    <span class="stat-value">{{ processing_summary.imputation.total_missing_after | number(0) }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Values Imputed</span>
                    <span class="stat-value">{{ processing_summary.imputation.total_imputed | number(0) }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Columns Processed</span>
                    <span class="stat-value">{{ processing_summary.imputation.columns_processed | length }}</span>
                </div>
            </div>
            {% endif %}

            {% if processing_summary.outliers %}
            <h3 class="subsection-title">Outlier Detection</h3>
            <div class="info-card">
                <div class="stat-row">
                    <span class="stat-label">Total Outliers Detected</span>
                    <span class="stat-value">{{ processing_summary.outliers.total_outliers_detected | number(0) }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Columns Processed</span>
                    <span class="stat-value">{{ processing_summary.outliers.columns_processed | length }}</span>
                </div>
            </div>
            {% endif %}

            {% if processing_summary.validation %}
            <h3 class="subsection-title">Data Validation</h3>
            <div class="info-card">
                <div class="stat-row">
                    <span class="stat-label">Total Violations</span>
                    <span class="stat-value">{{ processing_summary.validation.total_violations | number(0) }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Rules Applied</span>
                    <span class="stat-value">{{ processing_summary.validation.rules_applied | length }}</span>
                </div>
            </div>
            {% endif %}
        </div>
        {% endif %}

        <!-- Processing Steps -->
        <div class="section">
            <h2 class="section-title">Processing Workflow</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Step</th>
                            <th>Type</th>
                            <th>Status</th>
                            <th>Started</th>
                            <th>Completed</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for step in job_steps %}
                        <tr>
                            <td>{{ step.name }}</td>
                            <td>{{ step.get_step_type_display }}</td>
                            <td><span class="status-badge status-{{ step.status }}">{{ step.get_status_display }}</span></td>
                            <td>{{ step.started_at | datetime if step.started_at else 'N/A' }}</td>
                            <td>{{ step.completed_at | datetime if step.completed_at else 'N/A' }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Methodology -->
        <div class="section">
            <h2 class="section-title">Methodology</h2>
            <div class="methodology">
                <h4>Statistical Methods Applied:</h4>
                <ul>
                    <li><strong>Missing Value Imputation:</strong> Mean, median, and K-Nearest Neighbors (KNN) methods applied based on data characteristics</li>
                    <li><strong>Outlier Detection:</strong> Interquartile Range (IQR), Z-score, and Modified Z-score methods used for robust detection</li>
                    <li><strong>Survey Weight Application:</strong> Design weights applied with proper variance estimation and design effect calculations</li>
                    <li><strong>Confidence Intervals:</strong> Calculated using appropriate degrees of freedom and t-distribution</li>
                    <li><strong>Data Validation:</strong> Rule-based consistency checks and skip-pattern validation following survey methodology</li>
                </ul>
                
                <h4>Quality Assurance:</h4>
                <ul>
                    <li>All statistical calculations follow established methodological standards</li>
                    <li>Results are reproducible and fully documented</li>
                    <li>Processing workflow maintains complete audit trail</li>
                    <li>Data security and privacy maintained throughout processing</li>
                </ul>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>This report was automatically generated by the AI-Enhanced Survey Data Processing System</p>
            <p>Government of India | Ministry of Statistics and Programme Implementation</p>
            <p>Report Generated: {{ generation_time | datetime }}</p>
        </div>
    </div>
</body>
</html>'''
    
    def generate_dashboard_report(self, surveys_data, output_path):
        """
        Generate HTML dashboard showing multiple surveys overview.
        
        Args:
            surveys_data: List of survey data dictionaries
            output_path: Path to save the HTML file
        """
        try:
            logger.info("Generating HTML dashboard report")
            
            # Create dashboard template if it doesn't exist
            dashboard_template_path = os.path.join(self.template_dir, 'dashboard.html')
            if not os.path.exists(dashboard_template_path):
                self.create_dashboard_template()
            
            context = {
                'surveys': surveys_data,
                'generation_time': datetime.now(),
                'total_surveys': len(surveys_data),
                'total_records': sum(s.get('total_rows', 0) for s in surveys_data),
                'completed_jobs': len([s for s in surveys_data if s.get('status') == 'completed'])
            }
            
            template = self.env.get_template('dashboard.html')
            html_content = template.render(context)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Dashboard report generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating dashboard report: {str(e)}")
            raise
    
    def create_dashboard_template(self):
        """Create dashboard template for multiple surveys overview."""
        dashboard_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Survey Processing Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .dashboard {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #1976D2;
            margin-bottom: 10px;
        }
        
        .stat-label {
            color: #666;
            font-size: 1.1em;
        }
        
        .surveys-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .survey-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .survey-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #1976D2;
        }
        
        .survey-meta {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 15px;
        }
        
        .survey-stats {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        
        .survey-stat {
            text-align: center;
        }
        
        .survey-stat-number {
            font-weight: bold;
            color: #1976D2;
        }
        
        .survey-stat-label {
            font-size: 0.8em;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>Survey Data Processing Dashboard</h1>
            <p>Generated: {{ generation_time | datetime }}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{{ total_surveys }}</div>
                <div class="stat-label">Total Surveys</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ total_records | number(0) }}</div>
                <div class="stat-label">Total Records</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ completed_jobs }}</div>
                <div class="stat-label">Completed Jobs</div>
            </div>
        </div>
        
        <div class="surveys-grid">
            {% for survey in surveys %}
            <div class="survey-card">
                <div class="survey-title">{{ survey.name }}</div>
                <div class="survey-meta">
                    {{ survey.get_survey_type_display }} | {{ survey.created_at | datetime }}
                </div>
                <div class="survey-stats">
                    <div class="survey-stat">
                        <div class="survey-stat-number">{{ survey.total_rows | number(0) }}</div>
                        <div class="survey-stat-label">Records</div>
                    </div>
                    <div class="survey-stat">
                        <div class="survey-stat-number">{{ survey.total_columns | number(0) }}</div>
                        <div class="survey-stat-label">Variables</div>
                    </div>
                    <div class="survey-stat">
                        <div class="survey-stat-number">{{ 'Yes' if survey.has_weights else 'No' }}</div>
                        <div class="survey-stat-label">Weights</div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>'''
        
        dashboard_path = os.path.join(self.template_dir, 'dashboard.html')
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_template)