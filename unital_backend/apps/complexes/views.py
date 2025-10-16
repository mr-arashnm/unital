from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from .models import Complex, Building, Unit
from .serializers import ComplexSerializer, BuildingSerializer, UnitSerializer

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