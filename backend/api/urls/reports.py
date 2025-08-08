from django.urls import path
from api.views.reports import (
    ReportGenerationView, 
    ReportDownloadView, 
    ReportListView,
    report_templates_list,
    dashboard_report
)

urlpatterns = [
    path('generate/', ReportGenerationView.as_view(), name='report-generate'),
    path('templates/', report_templates_list, name='report-templates'),
    path('dashboard/', dashboard_report, name='dashboard-report'),
    path('list/', ReportListView.as_view(), name='report-list'),
    path('<uuid:report_id>/download/', ReportDownloadView.as_view(), name='report-download'),
]