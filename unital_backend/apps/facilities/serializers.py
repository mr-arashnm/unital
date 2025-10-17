from rest_framework import serializers
from .models import Facility, FacilityBooking, FacilityMaintenance, FacilityUsageRule, FacilityImage
from django.contrib.auth import get_user_model
from apps.complexes.serializers import UnitSerializer, BuildingSerializer  # تغییر نام

User = get_user_model()

class UserInfoSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'user_type', 'full_name']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

class FacilityImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilityImage
        fields = ['id', 'image', 'caption', 'is_primary', 'uploaded_at']

class FacilityUsageRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilityUsageRule
        fields = ['id', 'rule', 'is_mandatory', 'created_at']

class FacilitySerializer(serializers.ModelSerializer):
    building_info = BuildingSerializer(source='building', read_only=True)  # تغییر نام
    images = FacilityImageSerializer(many=True, read_only=True)
    usage_rules = FacilityUsageRuleSerializer(many=True, read_only=True)
    upcoming_bookings_count = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    
    class Meta:
        model = Facility
        fields = [
            'id', 'name', 'facility_type', 'description', 'building', 'building_info',  # تغییر نام
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

class FacilityDetailSerializer(serializers.ModelSerializer):
    building_info = BuildingSerializer(source='building', read_only=True)  # تغییر نام
    images = FacilityImageSerializer(many=True, read_only=True)
    usage_rules = FacilityUsageRuleSerializer(many=True, read_only=True)
    bookings = FacilityBookingSerializer(source='bookings', many=True, read_only=True)
    maintenance_records = FacilityMaintenanceSerializer(source='maintenance_records', many=True, read_only=True)
    
    class Meta:
        model = Facility
        fields = [
            'id', 'name', 'facility_type', 'description', 'building', 'building_info',  # تغییر نام
            'capacity', 'min_advance_booking', 'max_advance_booking',
            'opening_time', 'closing_time', 'rules', 'hourly_rate', 'is_free',
            'is_active', 'under_maintenance', 'images', 'usage_rules',
            'bookings', 'maintenance_records', 'created_at'
        ]

class FacilityBookingDetailSerializer(serializers.ModelSerializer):
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
    
    def validate(self, data):
        """
        Check that the facility is available for the requested time
        """
        facility = data.get('facility')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        # Check if facility is active and not under maintenance
        if not facility.is_active or facility.under_maintenance:
            raise serializers.ValidationError("Facility is not available for booking")
        
        # Check if the facility is open during the requested time
        if not facility.is_open_during(start_time, end_time):
            raise serializers.ValidationError("Facility is closed during the requested time")
        
        # Check for overlapping bookings
        overlapping_bookings = facility.bookings.filter(
            start_time__lt=end_time,
            end_time__gt=start_time,
            status__in=['confirmed', 'active']
        ).exists()
        
        if overlapping_bookings:
            raise serializers.ValidationError("Facility is already booked for the requested time")
        
        return data