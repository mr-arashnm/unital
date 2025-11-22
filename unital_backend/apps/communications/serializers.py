from rest_framework import serializers
from .models import (
    Notification, Meeting, MeetingAttendance, MeetingMinute,
    Announcement, SupportTicket, TicketResponse
)
from django.contrib.auth import get_user_model
from apps.complexes.serializers import UnitSerializer

User = get_user_model()

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # unique ref_name to avoid collisions with other apps
        ref_name = 'CommunicationsUserInfo'
        fields = ['id', 'first_name', 'last_name', 'email', 'user_type']

class NotificationSerializer(serializers.ModelSerializer):
    created_by_info = UserInfoSerializer(source='created_by', read_only=True)
    complex_name = serializers.CharField(source='complex.name', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'target_type',
            'specific_users', 'complex', 'complex_name', 'is_sent',
            'scheduled_at', 'sent_at', 'created_by', 'created_by_info',
            'created_at'
        ]

class MeetingAttendanceSerializer(serializers.ModelSerializer):
    user_info = UserInfoSerializer(source='user', read_only=True)
    
    class Meta:
        model = MeetingAttendance
        fields = [
            'id', 'user', 'user_info', 'status', 'responded_at',
            'actual_attendance'
        ]

class MeetingSerializer(serializers.ModelSerializer):
    created_by_info = UserInfoSerializer(source='created_by', read_only=True)
    complex_name = serializers.CharField(source='complex.name', read_only=True)
    attendees_info = MeetingAttendanceSerializer(source='meetingattendance_set', many=True, read_only=True)
    attendee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'meeting_type', 'description', 'agenda',
            'scheduled_date', 'location', 'duration', 'status',
            'attendees', 'attendees_info', 'attendee_count',
            'complex', 'complex_name', 'created_by', 'created_by_info',
            'created_at'
        ]
    
    def get_attendee_count(self, obj):
        return obj.attendees.count()

class MeetingMinuteSerializer(serializers.ModelSerializer):
    meeting_title = serializers.CharField(source='meeting.title', read_only=True)
    signed_by_info = UserInfoSerializer(source='signed_by', many=True, read_only=True)
    created_by_info = UserInfoSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = MeetingMinute
        fields = [
            'id', 'meeting', 'meeting_title', 'content', 'decisions',
            'action_items', 'signed_by', 'signed_by_info', 'created_by',
            'created_by_info', 'created_at'
        ]

class AnnouncementSerializer(serializers.ModelSerializer):
    created_by_info = UserInfoSerializer(source='created_by', read_only=True)
    complex_name = serializers.CharField(source='complex.name', read_only=True)
    target_units_info = UnitSerializer(source='target_units', many=True, read_only=True)
    
    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'content', 'priority', 'complex', 'complex_name',
            'target_units', 'target_units_info', 'is_published', 'publish_date',
            'expiry_date', 'created_by', 'created_by_info', 'created_at'
        ]

class TicketResponseSerializer(serializers.ModelSerializer):
    responded_by_info = UserInfoSerializer(source='responded_by', read_only=True)
    
    class Meta:
        model = TicketResponse
        fields = [
            'id', 'responded_by', 'responded_by_info', 'message',
            'attachment', 'is_internal', 'created_at'
        ]

class SupportTicketSerializer(serializers.ModelSerializer):
    submitted_by_info = UserInfoSerializer(source='submitted_by', read_only=True)
    unit_info = UnitSerializer(source='unit', read_only=True)
    assigned_to_info = UserInfoSerializer(source='assigned_to', read_only=True)
    responses = TicketResponseSerializer(many=True, read_only=True)
    
    class Meta:
        model = SupportTicket
        fields = [
            'id', 'title', 'description', 'ticket_type', 'status',
            'priority', 'submitted_by', 'submitted_by_info', 'unit', 'unit_info',
            'assigned_to', 'assigned_to_info', 'responses',
            'submitted_at', 'assigned_at', 'resolved_at', 'closed_at'
        ]