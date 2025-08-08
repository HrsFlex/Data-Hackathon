from django.urls import path
from api.views import UserProfileView, UserRegistrationView
from api.views.user_profile import user_stats, health_check

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('stats/', user_stats, name='user-stats'),
    path('health/', health_check, name='health-check'),
]