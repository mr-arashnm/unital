from rest_framework import serializers
from .models import Team, Task, ServiceRequest, TaskComment, Performance
from django.contrib.auth import get_user_model
from apps.complexes.serializers import UnitSerializer

User = get_user_model()

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'user_type']

class TeamSerializer(serializers.ModelSerializer):
    supervisor_info = UserInfoSerializer(source='supervisor', read_only=True)
    member_count = serializers.ReadOnlyField()
    members_info = UserInfoSerializer(source='members', many=True, read_only=True)
    
    class Meta:
        model = Team
        fields = [
            'id', 'name', 'team_type', 'description', 'complex',
            'supervisor', 'supervisor_info', 'members', 'members_info',
            'member_count', 'is_active', 'created_at'
        ]

class TaskCommentSerializer(serializers.ModelSerializer):
    author_info = UserInfoSerializer(source='author', read_only=True)
    
    class Meta:
        model = TaskComment
        fields = ['id', 'author', 'author_info', 'comment', 'attachment', 'created_at']

class TaskSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    assigned_to_info = UserInfoSerializer(source='assigned_to', read_only=True)
    related_unit_info = UnitSerializer(source='related_unit', read_only=True)
    created_by_info = UserInfoSerializer(source='created_by', read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'team', 'team_name',
            'assigned_to', 'assigned_to_info', 'priority', 'status',
            'due_date', 'estimated_hours', 'actual_hours',
            'related_unit', 'related_unit_info', 'created_by', 'created_by_info',
            'assigned_at', 'started_at', 'completed_at', 'comments',
            'created_at', 'updated_at'
        ]

class ServiceRequestSerializer(serializers.ModelSerializer):
    submitted_by_info = UserInfoSerializer(source='submitted_by', read_only=True)
    unit_info = UnitSerializer(source='unit', read_only=True)
    assigned_team_info = TeamSerializer(source='assigned_team', read_only=True)
    
    class Meta:
        model = ServiceRequest
        fields = [
            'id', 'title', 'description', 'request_type', 'status',
            'submitted_by', 'submitted_by_info', 'unit', 'unit_info',
            'priority', 'assigned_team', 'assigned_team_info', 'related_task',
            'submitted_at', 'assigned_at', 'completed_at'
        ]

class PerformanceSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    completion_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = Performance
        fields = [
            'id', 'team', 'team_name', 'period', 'total_tasks',
            'completed_tasks', 'overdue_tasks', 'completion_rate',
            'average_completion_time', 'satisfaction_rate', 'created_at'
        ]