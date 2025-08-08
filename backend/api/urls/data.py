from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import SurveyViewSet, SurveyUploadView, ProcessingJobViewSet

router = DefaultRouter()
router.register(r'surveys', SurveyViewSet, basename='survey')
router.register(r'processing-jobs', ProcessingJobViewSet, basename='processing-job')

urlpatterns = [
    path('upload/', SurveyUploadView.as_view(), name='survey-upload'),
    path('', include(router.urls)),
]