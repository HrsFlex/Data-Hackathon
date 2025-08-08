from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User

from api.models import UserProfile
from api.serializers import UserProfileSerializer, UserRegistrationSerializer


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)
        
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)
        
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                user = serializer.save()
                profile = user.profile
                
                response_data = {
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    },
                    'profile': UserProfileSerializer(profile).data,
                    'message': 'User registered successfully'
                }
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response(
                    {'error': f'Error creating user: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats(request):
    user = request.user
    
    stats = {
        'surveys_uploaded': user.surveys.count(),
        'processing_jobs': user.processing_jobs.count(),
        'completed_jobs': user.processing_jobs.filter(status='completed').count(),
        'failed_jobs': user.processing_jobs.filter(status='failed').count(),
        'pending_jobs': user.processing_jobs.filter(status='pending').count(),
    }
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({
        'status': 'healthy',
        'message': 'API is running successfully'
    })