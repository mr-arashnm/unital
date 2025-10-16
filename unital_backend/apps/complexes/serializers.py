from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Complex, Building, Unit

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