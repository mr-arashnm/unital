from django.contrib import admin
from .models import Team, Task, ServiceRequest, TaskComment, Performance

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'team_type', 'supervisor', 'is_active', 'created_at')
    list_filter = ('team_type', 'is_active')
    search_fields = ('name', 'supervisor__email', 'supervisor__first_name', 'supervisor__last_name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'team', 'assigned_to', 'priority', 'status', 'due_date', 'created_by')
    list_filter = ('priority', 'status', 'team')
    search_fields = ('title', 'team__name', 'assigned_to__email', 'created_by__email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'request_type', 'status', 'submitted_by', 'unit', 'assigned_team', 'submitted_at')
    list_filter = ('request_type', 'status', 'priority', 'assigned_team')
    search_fields = ('title', 'submitted_by__email', 'unit__unit_number')
    readonly_fields = ('submitted_at', 'assigned_at', 'completed_at')

@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at')
    search_fields = ('task__title', 'author__email', 'comment')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ('team', 'period', 'total_tasks', 'completed_tasks', 'overdue_tasks', 'satisfaction_rate')
    list_filter = ('period', 'team')
    readonly_fields = ('created_at', 'updated_at')