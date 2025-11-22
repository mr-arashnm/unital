from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from django.shortcuts import get_object_or_404

from .models import Building, Unit, Parking, Warehouse, Contract
from .serializers import (
    BuildingSerializer, BuildingDetailSerializer, UnitSerializer, UnitDetailSerializer,
    UnitTransferHistorySerializer, ParkingSerializer, WarehouseSerializer
)
from apps.accounts.models import User


# Note: this refactor aims to remove duplicates, keep consistent naming,
# and centralize building-scoped endpoints inside BuildingViewSet where appropriate.


class BuildingViewSet(viewsets.ModelViewSet):
    """Endpoints scoped to a Building.

    - list/retrieve/update buildings
    - building-scoped lists and create for units/parkings/warehouses
    - building-scoped detailed endpoints (unit detail, parking detail, warehouse detail)
    - transfer history endpoints for units inside a building
    """

    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BuildingDetailSerializer
        return BuildingSerializer

    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['manager', 'board_member']:
            return Building.objects.filter(board_members=user)
        elif user.user_type == 'owner':
            return Building.objects.filter(units__owner=user).distinct()
        elif user.user_type == 'resident':
            return Building.objects.filter(units__resident=user).distinct()
        return Building.objects.none()

    # building-scoped: list/create units
    @action(detail=True, methods=['get', 'post'], url_path='units')
    def units(self, request, pk=None):
        building = self.get_object()
        if request.method == 'GET':
            units = building.units.all()
            serializer = UnitSerializer(units, many=True)
            return Response(serializer.data)

        # POST: create unit in this building
        data = request.data.copy()
        data['building'] = building.id
        serializer = UnitSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # building-scoped: list/create parkings
    @action(detail=True, methods=['get', 'post'], url_path='parking')
    def parkings(self, request, pk=None):
        building = self.get_object()
        if request.method == 'GET':
            parkings = building.parkings.all()
            serializer = ParkingSerializer(parkings, many=True)
            return Response(serializer.data)

        # POST: create parking in this building
        data = request.data.copy()
        data['building'] = building.id
        serializer = ParkingSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # building-scoped: list/create warehouses
    @action(detail=True, methods=['get', 'post'], url_path='warehouse')
    def warehouses(self, request, pk=None):
        building = self.get_object()
        if request.method == 'GET':
            warehouses = building.warehouses.all()
            serializer = WarehouseSerializer(warehouses, many=True)
            return Response(serializer.data)
        # POST: create warehouse in this building
        data = request.data.copy()
        data['building'] = building.id
        serializer = WarehouseSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # building-scoped available
    @action(detail=True, methods=['get'], url_path='available-parking')
    def available_parkings(self, request, pk=None):
        building = self.get_object()
        parkings = building.parkings.filter(status='available')
        serializer = ParkingSerializer(parkings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='available-warehouse')
    def available_warehouses(self, request, pk=None):
        building = self.get_object()
        warehouses = building.warehouses.filter(status='available')
        serializer = WarehouseSerializer(warehouses, many=True)
        return Response(serializer.data)

    # building-scoped unit detail
    @action(detail=True, methods=['get', 'patch', 'put', 'delete'], url_path=r'units/(?P<unit_id>[^/.]+)')
    def unit_detail_in_building(self, request, pk=None, unit_id=None):
        unit = get_object_or_404(Unit, id=unit_id, building_id=pk)
        if request.method == 'GET':
            serializer = UnitDetailSerializer(unit)
            return Response(serializer.data)

        serializer = UnitDetailSerializer(unit, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # building-scoped transfer history
    @action(detail=True, methods=['get'], url_path=r'unit/(?P<unit_id>[^/.]+)/transfer-history')
    def unit_transfer_history_in_building(self, request, pk=None, unit_id=None):
        unit = get_object_or_404(Unit, id=unit_id, building_id=pk)
        history = unit.get_transfer_history()
        serializer = UnitTransferHistorySerializer(history, many=True)
        return Response({'unit': unit.full_address, 'transfer_history': serializer.data})

    @action(detail=True, methods=['get'], url_path=r'unit/(?P<unit_id>[^/.]+)/transfer-history/(?P<history_id>[^/.]+)')
    def unit_transfer_history_detail_in_building(self, request, pk=None, unit_id=None, history_id=None):
        unit = get_object_or_404(Unit, id=unit_id, building_id=pk)
        history = get_object_or_404(unit.transfer_history.model, id=history_id, unit=unit)
        serializer = UnitTransferHistorySerializer(history)
        return Response(serializer.data)

    # building-scoped parking detail with PATCH support
    @action(detail=True, methods=['get', 'patch', 'put', 'delete'], url_path=r'parking/(?P<parking_id>[^/.]+)')
    def parking_detail_in_building(self, request, pk=None, parking_id=None):
        parking = get_object_or_404(Parking, id=parking_id, building_id=pk)
        if request.method == 'GET':
            serializer = ParkingSerializer(parking)
            return Response(serializer.data)

        serializer = ParkingSerializer(parking, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # building-scoped warehouse detail with PATCH support
    @action(detail=True, methods=['get', 'patch', 'put', 'delete'], url_path=r'warehouse/(?P<warehouse_id>[^/.]+)')
    def warehouse_detail_in_building(self, request, pk=None, warehouse_id=None):
        warehouse = get_object_or_404(Warehouse, id=warehouse_id, building_id=pk)
        if request.method == 'GET':
            serializer = WarehouseSerializer(warehouse)
            return Response(serializer.data)

        serializer = WarehouseSerializer(warehouse, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


"""
class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UnitDetailSerializer
        return UnitSerializer

    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['manager', 'board_member']:
            return Unit.objects.filter(building__board_members=user)
        elif user.user_type == 'owner':
            return Unit.objects.filter(owner=user)
        elif user.user_type == 'resident':
            return Unit.objects.filter(resident=user)
        return Unit.objects.none()

    @action(detail=True, methods=['get'])
    def parkings(self, request, pk=None):
        unit = self.get_object()
        parkings = unit.assigned_parkings
        serializer = ParkingSerializer(parkings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'POST', 'PATCH', 'DELETE'])
    def warehouses(self, request, pk=None):
        unit = self.get_object()
        warehouses = unit.assigned_warehouses
        serializer = WarehouseSerializer(warehouses, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='available-parkings')
    def available_parkings(self, request, pk=None):
        unit = self.get_object()
        parkings = unit.get_available_parkings()
        serializer = ParkingSerializer(parkings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='available-warehouses')
    def available_warehouses(self, request, pk=None):
        unit = self.get_object()
        warehouses = unit.get_available_warehouses()
        serializer = WarehouseSerializer(warehouses, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign_parking(self, request, pk=None):
        unit = self.get_object()
        parking_code = request.data.get('parking_code')
        if not parking_code:
            return Response({'error': 'کد پارکینگ الزامی است'}, status=status.HTTP_400_BAD_REQUEST)
        if request.user.user_type not in ['manager', 'board_member']:
            return Response({'error': 'فقط مدیران می‌توانند پارکینگ تخصیص دهند'}, status=status.HTTP_403_FORBIDDEN)

        success, message = unit.assign_parking(parking_code)
        if success:
            return Response({'message': message})
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def release_parking(self, request, pk=None):
        unit = self.get_object()
        parking_code = request.data.get('parking_code')
        if not parking_code:
            return Response({'error': 'کد پارکینگ الزامی است'}, status=status.HTTP_400_BAD_REQUEST)
        if request.user.user_type not in ['manager', 'board_member']:
            return Response({'error': 'فقط مدیران می‌توانند پارکینگ آزاد کنند'}, status=status.HTTP_403_FORBIDDEN)

        success, message = unit.release_parking(parking_code)
        if success:
            return Response({'message': message})
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def assign_warehouse(self, request, pk=None):
        unit = self.get_object()
        warehouse_code = request.data.get('warehouse_code')
        if not warehouse_code:
            return Response({'error': 'کد انباری الزامی است'}, status=status.HTTP_400_BAD_REQUEST)
        if request.user.user_type not in ['manager', 'board_member']:
            return Response({'error': 'فقط مدیران می‌توانند انباری تخصیص دهند'}, status=status.HTTP_403_FORBIDDEN)

        success, message = unit.assign_warehouse(warehouse_code)
        if success:
            return Response({'message': message})
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def release_warehouse(self, request, pk=None):
        unit = self.get_object()
        warehouse_code = request.data.get('warehouse_code')
        if not warehouse_code:
            return Response({'error': 'کد انباری الزامی است'}, status=status.HTTP_400_BAD_REQUEST)
        if request.user.user_type not in ['manager', 'board_member']:
            return Response({'error': 'فقط مدیران می‌توانند انباری آزاد کنند'}, status=status.HTTP_403_FORBIDDEN)

        success, message = unit.release_warehouse(warehouse_code)
        if success:
            return Response({'message': message})
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)


class ParkingViewSet(viewsets.ModelViewSet):
    queryset = Parking.objects.all()
    serializer_class = ParkingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['manager', 'board_member']:
            return Parking.objects.filter(building__board_members=user)
        elif user.user_type == 'owner':
            return Parking.objects.filter(unit__owner=user)
        elif user.user_type == 'resident':
            return Parking.objects.filter(unit__resident=user)
        return Parking.objects.none()


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['manager', 'board_member']:
            return Warehouse.objects.filter(building__board_members=user)
        elif user.user_type == 'owner':
            return Warehouse.objects.filter(unit__owner=user)
        elif user.user_type == 'resident':
            return Warehouse.objects.filter(unit__resident=user)
        return Warehouse.objects.none()


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['manager', 'board_member']:
            return Contract.objects.filter(unit__building__board_members=user)
        elif user.user_type == 'owner':
            return Contract.objects.filter(unit__owner=user)
        elif user.user_type == 'resident':
            return Contract.objects.filter(unit__resident=user)
        return Contract.objects.none()

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        contract = self.get_object()
        if request.user.user_type not in ['manager', 'board_member']:
            return Response({'error': 'فقط مدیران می‌توانند قرارداد را فعال کنند'}, status=status.HTTP_403_FORBIDDEN)

        success, message = contract.activate_contract()
        if success:
            return Response({'message': message})
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
        
"""