from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Complex, Building, StorageAssignment, StorageUnit, Unit, UnitTransferHistory

# Use local lightweight serializer instead of importing from apps.accounts.serializers
User = get_user_model()

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # keep fields minimal and safe to avoid depending on account serializer internals
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'user_type']

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ['id', 'name', 'number', 'floors', 'units_per_floor']

class UnitSerializer(serializers.ModelSerializer):
    owner_info = UserInfoSerializer(source='owner', read_only=True)
    resident_info = UserInfoSerializer(source='current_resident', read_only=True)
    building_name = serializers.CharField(source='building.name', read_only=True)
    complex_name = serializers.CharField(source='building.complex.name', read_only=True)
    
    class Meta:
        model = Unit
        fields = [
            'id', 'unit_number', 'floor', 'area', 'status',
            'owner', 'owner_info', 'current_resident', 'resident_info',
            'building_name', 'complex_name', 'rooms', 'parking', 'storage',
            'created_at'
        ]

class ComplexSerializer(serializers.ModelSerializer):
    buildings = BuildingSerializer(many=True, read_only=True)
    board_members_info = UserInfoSerializer(source='board_members', many=True, read_only=True)
    total_occupied_units = serializers.SerializerMethodField()
    
    class Meta:
        model = Complex
        fields = [
            'id', 'name', 'code', 'type', 'address', 
            'total_units', 'total_buildings', 'description',
            'board_members', 'board_members_info', 'buildings',
            'total_occupied_units', 'created_at'
        ]
    
    def get_total_occupied_units(self, obj):
        return Unit.objects.filter(building__complex=obj, status='occupied').count()
    
class UnitTransferHistorySerializer(serializers.ModelSerializer):
    previous_owner_info = UserInfoSerializer(source='previous_owner', read_only=True)
    new_owner_info = UserInfoSerializer(source='new_owner', read_only=True)
    previous_resident_info = UserInfoSerializer(source='previous_resident', read_only=True)
    new_resident_info = UserInfoSerializer(source='new_resident', read_only=True)
    unit_info = UnitSerializer(source='unit', read_only=True)
    
    class Meta:
        model = UnitTransferHistory
        fields = [
            'id', 'unit', 'unit_info', 'transfer_type', 'transfer_date',
            'previous_owner', 'previous_owner_info', 'new_owner', 'new_owner_info',
            'previous_resident', 'previous_resident_info', 'new_resident', 'new_resident_info',
            'contract_number', 'contract_date', 'description', 'recorded_by', 'created_at'
        ]
        
        
class StorageUnitSerializer(serializers.ModelSerializer):
    complex_name = serializers.CharField(source='complex.name', read_only=True)
    assigned_unit_info = UnitSerializer(source='assigned_unit', read_only=True)
    
    class Meta:
        model = StorageUnit
        fields = [
            'id', 'complex', 'complex_name', 'storage_type', 'unit_number', 'name',
            'location', 'area', 'capacity', 'features', 'status', 'assigned_unit',
            'assigned_unit_info', 'monthly_fee', 'is_covered', 'has_electricity',
            'has_lighting', 'full_code', 'is_available', 'created_at'
        ]

class StorageAssignmentSerializer(serializers.ModelSerializer):
    storage_unit_info = StorageUnitSerializer(source='storage_unit', read_only=True)
    unit_info = UnitSerializer(source='unit', read_only=True)
    created_by_info = UnitSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = StorageAssignment
        fields = [
            'id', 'storage_unit', 'storage_unit_info', 'unit', 'unit_info',
            'assignment_type', 'start_date', 'end_date', 'is_active',
            'monthly_fee', 'is_included_in_charge', 'contract_number',
            'description', 'created_by', 'created_by_info', 'created_at'
        ]