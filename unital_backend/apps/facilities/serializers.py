from rest_framework import serializers
from .models import Facility, FacilityBooking, FacilityMaintenance, FacilityUsageRule, FacilityImage
from django.contrib.auth import get_user_model
from apps.complexes.serializers import UnitSerializer, ComplexSerializer

User = get_user_model()

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'user_type']

class FacilityImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilityImage
        fields = ['id', 'image', 'caption', 'is_primary', 'uploaded_at']

class FacilityUsageRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilityUsageRule
        fields = ['id', 'rule', 'is_mandatory', 'created_at']

class FacilitySerializer(serializers.ModelSerializer):
    complex_info = ComplexSerializer(source='complex', read_only=True)
    images = FacilityImageSerializer(many=True, read_only=True)
    usage_rules = FacilityUsageRuleSerializer(many=True, read_only=True)
    upcoming_bookings_count = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    
    class Meta:
        model = Facility
        fields = [
            'id', 'name', 'facility_type', 'description', 'complex', 'complex_info',
            'capacity', 'min_advance_booking', 'max_advance_booking',
            'opening_time', 'closing_time', 'rules', 'hourly_rate', 'is_free',
            'is_active', 'under_maintenance', 'images', 'usage_rules',
            'upcoming_bookings_count', 'is_available', 'created_at'
        ]
    
    def get_upcoming_bookings_count(self, obj):
        from django.utils import timezone
        return obj.bookings.filter(
            start_time__gte=timezone.now(),
            status__in=['confirmed', 'active']
        ).count()
    
    def get_is_available(self, obj):
        return obj.is_active and not obj.under_maintenance

class FacilityBookingSerializer(serializers.ModelSerializer):
    facility_info = FacilitySerializer(source='facility', read_only=True)
    user_info = UserInfoSerializer(source='user', read_only=True)
    approved_by_info = UserInfoSerializer(source='approved_by', read_only=True)
    
    class Meta:
        model = FacilityBooking
        fields = [
            'id', 'facility', 'facility_info', 'user', 'user_info',
            'start_time', 'end_time', 'duration_hours', 'purpose',
            'participants_count', 'special_requirements', 'status',
            'approved_by', 'approved_by_info', 'approved_at', 'total_cost',
            'is_paid', 'created_at'
        ]

class FacilityMaintenanceSerializer(serializers.ModelSerializer):
    facility_info = FacilitySerializer(source='facility', read_only=True)
    assigned_to_info = UserInfoSerializer(source='assigned_to', read_only=True)
    created_by_info = UserInfoSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = FacilityMaintenance
        fields = [
            'id', 'facility', 'facility_info', 'title', 'maintenance_type',
            'description', 'priority', 'scheduled_start', 'scheduled_end',
            'actual_start', 'actual_end', 'status', 'assigned_to', 'assigned_to_info',
            'affect_bookings', 'created_by', 'created_by_info', 'created_at'
        ]