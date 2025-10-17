from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from .models import Building, Unit, Parking, Warehouse, Contract
from .serializers import (
    BuildingSerializer, BuildingDetailSerializer, UnitSerializer, UnitDetailSerializer, 
    UnitTransferHistorySerializer, ContractSerializer, ParkingSerializer, WarehouseSerializer
)
from apps.accounts.models import User

class BuildingViewSet(viewsets.ModelViewSet):
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
            # مالک واحدهایی که داره
            return Building.objects.filter(
                units__owner=user
            ).distinct()
        elif user.user_type == 'resident':
            # ساکن واحدهایی که ساکنش هست
            return Building.objects.filter(
                units__resident=user
            ).distinct()
        else:
            return Building.objects.none()
    
    @action(detail=True, methods=['get'])
    def units(self, request, pk=None):
        building = self.get_object()
        units = building.units.all()
        serializer = UnitSerializer(units, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def parkings(self, request, pk=None):
        building = self.get_object()
        parkings = building.parkings.all()
        serializer = ParkingSerializer(parkings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def warehouses(self, request, pk=None):
        building = self.get_object()
        warehouses = building.warehouses.all()
        serializer = WarehouseSerializer(warehouses, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def available_parkings(self, request, pk=None):
        building = self.get_object()
        parkings = building.parkings.filter(status='available')
        serializer = ParkingSerializer(parkings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def available_warehouses(self, request, pk=None):
        building = self.get_object()
        warehouses = building.warehouses.filter(status='available')
        serializer = WarehouseSerializer(warehouses, many=True)
        return Response(serializer.data)

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
        else:
            return Unit.objects.none()
    
    @action(detail=True, methods=['get'])
    def parkings(self, request, pk=None):
        unit = self.get_object()
        parkings = unit.assigned_parkings
        serializer = ParkingSerializer(parkings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def warehouses(self, request, pk=None):
        unit = self.get_object()
        warehouses = unit.assigned_warehouses
        serializer = WarehouseSerializer(warehouses, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def available_parkings(self, request, pk=None):
        unit = self.get_object()
        parkings = unit.get_available_parkings()
        serializer = ParkingSerializer(parkings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
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
            return Response(
                {'error': 'کد پارکینگ الزامی است'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # فقط مدیران می‌توانند پارکینگ تخصیص دهند
        if request.user.user_type not in ['manager', 'board_member']:
            return Response(
                {'error': 'فقط مدیران می‌توانند پارکینگ تخصیص دهند'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        success, message = unit.assign_parking(parking_code)
        
        if success:
            return Response({'message': message})
        else:
            return Response(
                {'error': message}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def release_parking(self, request, pk=None):
        unit = self.get_object()
        parking_code = request.data.get('parking_code')
        
        if not parking_code:
            return Response(
                {'error': 'کد پارکینگ الزامی است'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # فقط مدیران می‌توانند پارکینگ آزاد کنند
        if request.user.user_type not in ['manager', 'board_member']:
            return Response(
                {'error': 'فقط مدیران می‌توانند پارکینگ آزاد کنند'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        success, message = unit.release_parking(parking_code)
        
        if success:
            return Response({'message': message})
        else:
            return Response(
                {'error': message}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def assign_warehouse(self, request, pk=None):
        unit = self.get_object()
        warehouse_code = request.data.get('warehouse_code')
        
        if not warehouse_code:
            return Response(
                {'error': 'کد انباری الزامی است'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # فقط مدیران می‌توانند انباری تخصیص دهند
        if request.user.user_type not in ['manager', 'board_member']:
            return Response(
                {'error': 'فقط مدیران می‌توانند انباری تخصیص دهند'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        success, message = unit.assign_warehouse(warehouse_code)
        
        if success:
            return Response({'message': message})
        else:
            return Response(
                {'error': message}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def release_warehouse(self, request, pk=None):
        unit = self.get_object()
        warehouse_code = request.data.get('warehouse_code')
        
        if not warehouse_code:
            return Response(
                {'error': 'کد انباری الزامی است'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # فقط مدیران می‌توانند انباری آزاد کنند
        if request.user.user_type not in ['manager', 'board_member']:
            return Response(
                {'error': 'فقط مدیران می‌توانند انباری آزاد کنند'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        success, message = unit.release_warehouse(warehouse_code)
        
        if success:
            return Response({'message': message})
        else:
            return Response(
                {'error': message}, 
                status=status.HTTP_400_BAD_REQUEST
            )

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
        else:
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
        else:
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
        else:
            return Contract.objects.none()
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        contract = self.get_object()
        
        # فقط مدیران می‌توانند قرارداد را فعال کنند
        if request.user.user_type not in ['manager', 'board_member']:
            return Response(
                {'error': 'فقط مدیران می‌توانند قرارداد را فعال کنند'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        success, message = contract.activate_contract()
        
        if success:
            return Response({'message': message})
        else:
            return Response(
                {'error': message}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unit_transfer_history(request, unit_id):
    """دریافت تاریخچه انتقالات یک واحد"""
    try:
        unit = Unit.objects.get(id=unit_id)
        
        # بررسی دسترسی کاربر
        user = request.user
        if user.user_type not in ['manager', 'board_member'] and user not in [unit.owner, unit.resident]:
            return Response(
                {'error': 'دسترسی غیرمجاز'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        history = unit.get_transfer_history()
        serializer = UnitTransferHistorySerializer(history, many=True)
        
        return Response({
            'unit': unit.full_address,
            'transfer_history': serializer.data
        })
        
    except Unit.DoesNotExist:
        return Response(
            {'error': 'واحد یافت نشد'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_unit_ownership(request, unit_id):
    """تغییر مالکیت واحد"""
    try:
        unit = Unit.objects.get(id=unit_id)
        new_owner_id = request.data.get('new_owner_id')
        transfer_date = request.data.get('transfer_date')
        
        if not all([new_owner_id, transfer_date]):
            return Response(
                {'error': 'مالک جدید و تاریخ انتقال الزامی است'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # فقط مدیران می‌توانند مالکیت را تغییر دهند
        if request.user.user_type not in ['manager', 'board_member']:
            return Response(
                {'error': 'فقط مدیران می‌توانند مالکیت را تغییر دهند'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_owner = User.objects.get(id=new_owner_id, user_type__in=['owner', 'resident'])
        
        unit.change_ownership(
            new_owner=new_owner,
            transfer_date=transfer_date,
            contract_number=request.data.get('contract_number'),
            description=request.data.get('description'),
            recorded_by=request.user
        )
        
        return Response({
            'message': 'مالکیت واحد با موفقیت تغییر یافت',
            'new_owner': f'{new_owner.first_name} {new_owner.last_name}'
        })
        
    except (Unit.DoesNotExist, User.DoesNotExist) as e:
        return Response(
            {'error': 'واحد یا کاربر یافت نشد'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_unit_residency(request, unit_id):
    """تغییر سکونت واحد"""
    try:
        unit = Unit.objects.get(id=unit_id)
        new_resident_id = request.data.get('new_resident_id')
        transfer_date = request.data.get('transfer_date')
        
        if not all([new_resident_id, transfer_date]):
            return Response(
                {'error': 'ساکن جدید و تاریخ انتقال الزامی است'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # فقط مدیران می‌توانند سکونت را تغییر دهند
        if request.user.user_type not in ['manager', 'board_member']:
            return Response(
                {'error': 'فقط مدیران می‌توانند سکونت را تغییر دهند'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_resident = User.objects.get(id=new_resident_id, user_type__in=['owner', 'resident'])
        
        unit.change_residency(
            new_resident=new_resident,
            transfer_date=transfer_date,
            description=request.data.get('description'),
            recorded_by=request.user
        )
        
        return Response({
            'message': 'سکونت واحد با موفقیت تغییر یافت',
            'new_resident': f'{new_resident.first_name} {new_resident.last_name}'
        })
        
    except (Unit.DoesNotExist, User.DoesNotExist) as e:
        return Response(
            {'error': 'واحد یا کاربر یافت نشد'}, 
            status=status.HTTP_404_NOT_FOUND
        )