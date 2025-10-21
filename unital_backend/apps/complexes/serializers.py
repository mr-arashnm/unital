from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Building, Unit, UnitTransferHistory, Parking, Warehouse, Contract

User = get_user_model()


class UserInfoSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'user_type', 'full_name']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = [
            'id', 'name', 'code', 'type', 'address',
            'total_floors', 'total_units',
            'total_parkings', 'total_warehouses',
            'description', 'created_at', 'updated_at'
        ]


class UnitSerializer(serializers.ModelSerializer):
    owner_info = UserInfoSerializer(source='owner', read_only=True)
    resident_info = UserInfoSerializer(source='resident', read_only=True)
    building_info = BuildingSerializer(source='building', read_only=True)

    class Meta:
        model = Unit
        fields = [
            'id', 'unit_number', 'floor', 'area', 'status',
            'owner', 'owner_info', 'resident', 'resident_info',
            'building', 'building_info', 'rooms',
            'has_parking', 'has_warehouse',
            'total_parking_count', 'total_warehouse_count',
            'full_address', 'created_at', 'updated_at'
        ]


class ParkingSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source='building.name', read_only=True)
    unit_info = UnitSerializer(source='unit', read_only=True)

    class Meta:
        model = Parking
        fields = [
            'id', 'building', 'building_name', 'unit', 'unit_info',
            'floor', 'code', 'status', 'created_at', 'updated_at'
        ]


class WarehouseSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source='building.name', read_only=True)
    unit_info = UnitSerializer(source='unit', read_only=True)

    class Meta:
        model = Warehouse
        fields = [
            'id', 'building', 'building_name', 'unit', 'unit_info',
            'floor', 'code', 'status', 'area', 'created_at', 'updated_at'
        ]


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
            'contract_number', 'contract_date', 'description', 'recorded_by',
            'created_at', 'updated_at'
        ]


class ContractSerializer(serializers.ModelSerializer):
    unit_info = UnitSerializer(source='unit', read_only=True)
    first_party_info = UserInfoSerializer(source='first_party', read_only=True)
    second_party_info = UserInfoSerializer(source='second_party', read_only=True)
    created_by_info = UserInfoSerializer(source='created_by', read_only=True)

    class Meta:
        model = Contract
        fields = [
            'id', 'unit', 'unit_info', 'contract_type', 'contract_number', 'title',
            'first_party', 'first_party_info', 'second_party', 'second_party_info',
            'start_date', 'end_date', 'duration_months', 'amount', 'deposit_amount',
            'status', 'first_party_signed', 'second_party_signed', 'signed_date',
            'contract_file', 'description', 'created_by', 'created_by_info',
            'created_at', 'updated_at'
        ]


class BuildingDetailSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True, read_only=True)
    parkings = ParkingSerializer(many=True, read_only=True)
    warehouses = WarehouseSerializer(many=True, read_only=True)
    board_members_info = UserInfoSerializer(many=True, read_only=True, source='board_members')
    total_occupied_units = serializers.SerializerMethodField()
    available_parkings = serializers.SerializerMethodField()
    available_warehouses = serializers.SerializerMethodField()

    class Meta:
        model = Building
        fields = [
            'id', 'name', 'code', 'type', 'address',
            'total_floors', 'total_units', 'total_parkings', 'total_warehouses', 'description',
            'board_members', 'board_members_info',
            'units', 'parkings', 'warehouses',
            'total_occupied_units', 'available_parkings', 'available_warehouses',
            'created_at', 'updated_at'
        ]

    def get_total_occupied_units(self, obj):
        return obj.units.filter(status='occupied').count()

    def get_available_parkings(self, obj):
        return obj.parkings.filter(status='available').count()

    def get_available_warehouses(self, obj):
        return obj.warehouses.filter(status='available').count()


class UnitDetailSerializer(serializers.ModelSerializer):
    owner_info = UserInfoSerializer(source='owner', read_only=True)
    resident_info = UserInfoSerializer(source='resident', read_only=True)
    building_info = BuildingSerializer(source='building', read_only=True)
    parkings_info = ParkingSerializer(many=True, read_only=True)
    warehouses_info = WarehouseSerializer(many=True, read_only=True)
    transfer_history = UnitTransferHistorySerializer(many=True, read_only=True)
    contracts = ContractSerializer(many=True, read_only=True)

    class Meta:
        model = Unit
        fields = [
            'id', 'unit_number', 'floor', 'area', 'status',
            'owner', 'owner_info', 'resident', 'resident_info',
            'building', 'building_info', 'rooms',
            'parkings_info', 'warehouses_info',
            'has_parking', 'has_warehouse',
            'total_parking_count', 'total_warehouse_count',
            'full_address', 'created_at', 'updated_at',
            'transfer_history', 'contracts'
        ]