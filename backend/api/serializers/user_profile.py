from rest_framework import serializers
from django.contrib.auth.models import User
from api.models import UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    display_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'display_name', 'organization', 'organization_type',
            'department', 'phone', 'bio', 'preferred_language', 'timezone',
            'notification_preferences', 'api_access_level', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'api_access_level']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    organization = serializers.CharField(required=False, allow_blank=True)
    organization_type = serializers.ChoiceField(
        choices=UserProfile.ORGANIZATION_TYPES,
        required=False,
        allow_blank=True
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'password', 'password_confirm', 'organization', 'organization_type'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        organization = validated_data.pop('organization', '')
        organization_type = validated_data.pop('organization_type', '')
        
        user = User.objects.create_user(**validated_data)
        
        UserProfile.objects.create(
            user=user,
            organization=organization,
            organization_type=organization_type
        )
        
        return user