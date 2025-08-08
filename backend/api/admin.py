from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Survey, SurveyColumn, ProcessingJob, ProcessingStep, UserProfile


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ['name', 'survey_type', 'uploaded_by', 'file_type', 'total_rows', 'total_columns', 'created_at']
    list_filter = ['survey_type', 'file_type', 'has_weights', 'created_at']
    search_fields = ['name', 'description', 'uploaded_by__username']
    readonly_fields = ['id', 'file_size', 'total_rows', 'total_columns', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'survey_type', 'uploaded_by')
        }),
        ('File Information', {
            'fields': ('original_file', 'file_type', 'file_size', 'total_rows', 'total_columns')
        }),
        ('Weight Information', {
            'fields': ('has_weights', 'weight_column')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SurveyColumn)
class SurveyColumnAdmin(admin.ModelAdmin):
    list_display = ['name', 'survey', 'data_type', 'is_required', 'is_weight', 'missing_count', 'position']
    list_filter = ['data_type', 'is_required', 'is_weight', 'survey__survey_type']
    search_fields = ['name', 'original_name', 'survey__name']
    ordering = ['survey', 'position']


@admin.register(ProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'survey', 'user', 'status', 'progress_percentage', 'created_at', 'duration']
    list_filter = ['status', 'created_at', 'survey__survey_type']
    search_fields = ['survey__name', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'duration']
    
    def duration(self, obj):
        return obj.duration
    duration.short_description = 'Duration'


@admin.register(ProcessingStep)
class ProcessingStepAdmin(admin.ModelAdmin):
    list_display = ['job', 'name', 'step_type', 'status', 'order', 'started_at', 'completed_at']
    list_filter = ['step_type', 'status', 'started_at']
    search_fields = ['name', 'job__survey__name']
    ordering = ['job', 'order']


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'organization_type', 'api_access_level', 'created_at']
    list_filter = ['organization_type', 'api_access_level', 'created_at']
    search_fields = ['user__username', 'user__email', 'organization']