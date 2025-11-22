from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Building, Unit, UnitTransferHistory, Parking, Warehouse, Contract

User = get_user_model()

# not use
class UserInfoSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        # avoid referencing removed `username` field and provide a unique
        # component name so drf-spectacular does not collide with other
        # UserInfo serializers across apps
        ref_name = 'ComplexesUserInfo'
        fields = ['id', 'first_name', 'last_name', 'email', 'user_type', 'full_name']

    def get_full_name(self, obj):
        # User model in this project does not include `username`.
        # fall back to email if names are empty.
        return f"{obj.first_name} {obj.last_name}".strip() or getattr(obj, 'email', '')


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ["id", "name", "address", "type"]


class UnitSerializer(serializers.ModelSerializer):

    class Meta:
        model = Unit
        fields = ['id', 'unit_number', 'floor', 'area']


class ParkingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Parking
        fields = ['id', 'floor', 'code', 'status']

# not use
class ParkingDetailSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source='building.name', read_only=True)
    unit_info = UnitSerializer(source='unit', read_only=True)

    class Meta:
        model = Parking
        fields = [
            'id', 'building', 'building_name', 'unit', 'unit_info',
            'floor', 'code', 'status', 'created_at', 'updated_at'
        ]


class WarehouseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Warehouse
        fields = ['id', 'floor', 'code', 'area', 'status']

# not use
class WarehouseDetailSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source='building.name', read_only=True)
    unit_info = UnitSerializer(source='unit', read_only=True)

    class Meta:
        model = Warehouse
        fields = [
            'id', 'building', 'building_name', 'unit', 'unit_info',
            'floor', 'code', 'status', 'area', 'created_at', 'updated_at'
        ]


class UnitDetailSerializer(serializers.ModelSerializer):
    parking = ParkingSerializer(source='parkings', read_only=True, many=True)
    warehouse = WarehouseSerializer(source='warehouses', read_only=True, many=True)

    class Meta:
        model = Unit
        fields = [
            'id', 'unit_number', 'floor', 'area', 'status',
            'owner', 'resident',
            'rooms',
            'parking',
            'warehouse',
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


    class Meta:
        model = Building
        fields = [
            'id', 'name', 'address', 'type', 'created_at',
            'total_floors', 'total_units', 'total_parkings', 'total_warehouses', 'description',
            'units', 'parkings', 'warehouses',
        ]
