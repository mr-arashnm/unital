from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Facility, FacilityBooking, FacilityMaintenance, FacilityUsageRule, FacilityImage
from .serializers import (
    FacilitySerializer, FacilityBookingSerializer, 
    FacilityMaintenanceSerializer, FacilityUsageRuleSerializer,
    FacilityImageSerializer
)

class FacilityViewSet(viewsets.ModelViewSet):
    queryset = Facility.objects.filter(is_active=True)
    serializer_class = FacilitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        complex_id = self.request.query_params.get('complex_id')
        
        if user.user_type in ['manager', 'board_member', 'staff']:
            queryset = Facility.objects.filter(complex__board_members=user)
        else:
            # ساکنین فقط امکانات مجتمع خود را می‌بینند
            user_units = user.owned_units.all() | user.residing_units.all()
            user_complexes = user_units.values_list('building__complex', flat=True)
            queryset = Facility.objects.filter(complex_id__in=user_complexes, is_active=True)
        
        if complex_id:
            queryset = queryset.filter(complex_id=complex_id)
            
        return queryset
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """بررسی موجودی یک امکان در تاریخ خاص"""
        facility = self.get_object()
        date_str = request.query_params.get('date')
        
        if not date_str:
            return Response(
                {'error': 'پارامتر date الزامی است (YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'فرمت تاریخ نامعتبر است. از YYYY-MM-DD استفاده کنید'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # بررسی تعمیرات
        maintenance = FacilityMaintenance.objects.filter(
            facility=facility,
            scheduled_start__date=target_date,
            status__in=['pending', 'confirmed', 'active']
        ).exists()
        
        if maintenance:
            return Response({
                'date': target_date,
                'available': False,
                'reason': 'امکان در دست تعمیر است'
            })
        
        # دریافت رزروهای موجود
        bookings = FacilityBooking.objects.filter(
            facility=facility,
            start_time__date=target_date,
            status__in=['confirmed', 'active']
        )
        
        # محاسبه ساعات اشغال شده
        booked_slots = []
        for booking in bookings:
            booked_slots.append({
                'start': booking.start_time.time(),
                'end': booking.end_time.time()
            })
        
        return Response({
            'date': target_date,
            'available': True,
            'booked_slots': booked_slots,
            'opening_time': facility.opening_time,
            'closing_time': facility.closing_time
        })
    
    @action(detail=True, methods=['get'])
    def time_slots(self, request, pk=None):
        """دریافت ساعات خالی برای رزرو"""
        facility = self.get_object()
        date_str = request.query_params.get('date')
        
        if not date_str:
            return Response(
                {'error': 'پارامتر date الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # اینجا می‌توانید منطق محاسبه ساعات خالی را پیاده‌سازی کنید
        # برای سادگی، تمام ساعات کاری را برمی‌گردانیم
        return Response({
            'date': date_str,
            'available_slots': [
                {'start': '08:00', 'end': '10:00'},
                {'start': '10:00', 'end': '12:00'},
                {'start': '14:00', 'end': '16:00'},
                {'start': '16:00', 'end': '18:00'},
                {'start': '18:00', 'end': '20:00'},
            ]
        })

class FacilityBookingViewSet(viewsets.ModelViewSet):
    queryset = FacilityBooking.objects.all()
    serializer_class = FacilityBookingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type in ['manager', 'board_member', 'staff']:
            return FacilityBooking.objects.filter(facility__complex__board_members=user)
        else:
            return FacilityBooking.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """تأیید رزرو توسط مدیریت"""
        booking = self.get_object()
        
        if booking.status != 'pending':
            return Response(
                {'error': 'این رزرو قبلاً تأیید یا رد شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # بررسی تداخل زمانی
        conflicting_booking = FacilityBooking.objects.filter(
            facility=booking.facility,
            start_time__lt=booking.end_time,
            end_time__gt=booking.start_time,
            status__in=['confirmed', 'active']
        ).exclude(id=booking.id).exists()
        
        if conflicting_booking:
            return Response(
                {'error': 'تداخل زمانی با رزرو دیگری وجود دارد'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'confirmed'
        booking.approved_by = request.user
        booking.approved_at = timezone.now()
        booking.save()
        
        return Response({'message': 'رزرو با موفقیت تأیید شد'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """رد درخواست رزرو"""
        booking = self.get_object()
        
        if booking.status != 'pending':
            return Response(
                {'error': 'این رزرو قبلاً تأیید یا رد شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', 'بدون دلیل')
        booking.status = 'rejected'
        booking.approved_by = request.user
        booking.approved_at = timezone.now()
        booking.save()
        
        return Response({'message': f'رزرو رد شد. دلیل: {reason}'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """لغو رزرو توسط کاربر"""
        booking = self.get_object()
        
        if booking.user != request.user:
            return Response(
                {'error': 'شما مجاز به لغو این رزرو نیستید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status not in ['pending', 'confirmed']:
            return Response(
                {'error': 'امکان لغو این رزرو وجود ندارد'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'cancelled'
        booking.save()
        
        return Response({'message': 'رزرو با موفقیت لغو شد'})
    
    @action(detail=False, methods=['get'])
    def my_bookings(self, request):
        """رزروهای کاربر جاری"""
        bookings = FacilityBooking.objects.filter(user=request.user)
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)

class FacilityMaintenanceViewSet(viewsets.ModelViewSet):
    queryset = FacilityMaintenance.objects.all()
    serializer_class = FacilityMaintenanceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type in ['manager', 'board_member', 'staff']:
            return FacilityMaintenance.objects.filter(facility__complex__board_members=user)
        return FacilityMaintenance.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """شروع تعمیرات"""
        maintenance = self.get_object()
        
        if maintenance.status != 'confirmed':
            return Response(
                {'error': 'فقط تعمیرات تأیید شده قابل شروع هستند'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        maintenance.status = 'active'
        maintenance.actual_start = timezone.now()
        maintenance.save()
        
        # غیرفعال کردن موقت امکان
        facility = maintenance.facility
        facility.under_maintenance = True
        facility.save()
        
        # لغو رزروهای آینده اگر تأثیر داشته باشد
        if maintenance.affect_bookings:
            FacilityBooking.objects.filter(
                facility=facility,
                start_time__gte=maintenance.actual_start,
                status__in=['pending', 'confirmed']
            ).update(status='cancelled')
        
        return Response({'message': 'تعمیرات شروع شد'})
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """اتمام تعمیرات"""
        maintenance = self.get_object()
        
        if maintenance.status != 'active':
            return Response(
                {'error': 'فقط تعمیرات فعال قابل تکمیل هستند'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        maintenance.status = 'completed'
        maintenance.actual_end = timezone.now()
        maintenance.save()
        
        # فعال کردن مجدد امکان
        facility = maintenance.facility
        facility.under_maintenance = False
        facility.save()
        
        return Response({'message': 'تعمیرات تکمیل شد'})

class FacilityUsageRuleViewSet(viewsets.ModelViewSet):
    queryset = FacilityUsageRule.objects.all()
    serializer_class = FacilityUsageRuleSerializer
    permission_classes = [IsAuthenticated]

class FacilityImageViewSet(viewsets.ModelViewSet):
    queryset = FacilityImage.objects.all()
    serializer_class = FacilityImageSerializer
    permission_classes = [IsAuthenticated]