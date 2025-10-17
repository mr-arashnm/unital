from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from .models import Complex, Building, Unit
from .serializers import ComplexSerializer, BuildingSerializer, UnitSerializer, UnitTransferHistorySerializer
from apps.accounts.models import User

class ComplexViewSet(viewsets.ModelViewSet):
    queryset = Complex.objects.all()
    serializer_class = ComplexSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # کاربر فقط مجتمع‌هایی رو می‌بینه که عضوش هست
        user = self.request.user
        if user.user_type in ['manager', 'board_member']:
            return Complex.objects.filter(board_members=user)
        elif user.user_type == 'owner':
            # مالک واحدهایی که داره
            return Complex.objects.filter(
                buildings__units__owner=user
            ).distinct()
        elif user.user_type == 'resident':
            # ساکن واحدهایی که ساکنش هست
            return Complex.objects.filter(
                buildings__units__current_resident=user
            ).distinct()
        else:
            return Complex.objects.none()
    
    @action(detail=True, methods=['get'])
    def buildings(self, request, pk=None):
        complex = self.get_object()
        buildings = complex.buildings.all()
        serializer = BuildingSerializer(buildings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def units(self, request, pk=None):
        complex = self.get_object()
        units = Unit.objects.filter(building__complex=complex)
        serializer = UnitSerializer(units, many=True)
        return Response(serializer.data)

class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Building.objects.filter(complex__board_members=user)

class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['manager', 'board_member']:
            return Unit.objects.filter(building__complex__board_members=user)
        elif user.user_type == 'owner':
            return Unit.objects.filter(owner=user)
        elif user.user_type == 'resident':
            return Unit.objects.filter(current_resident=user)
        else:
            return Unit.objects.none()
        
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unit_transfer_history(request, unit_id):
    """دریافت تاریخچه انتقالات یک واحد"""
    try:
        unit = Unit.objects.get(id=unit_id)
        
        # بررسی دسترسی کاربر
        user = request.user
        if user.user_type not in ['manager', 'board_member'] and user not in [unit.owner, unit.current_resident]:
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