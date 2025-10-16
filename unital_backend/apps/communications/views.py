from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import (
    Notification, Meeting, MeetingAttendance, MeetingMinute,
    Announcement, SupportTicket, TicketResponse
)
from .serializers import (
    NotificationSerializer, MeetingSerializer, MeetingAttendanceSerializer,
    MeetingMinuteSerializer, AnnouncementSerializer, SupportTicketSerializer,
    TicketResponseSerializer
)

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        complex_id = self.request.query_params.get('complex_id')
        
        # مدیران می‌توانند همه اطلاع‌رسانی‌ها را ببینند
        if user.user_type in ['manager', 'board_member']:
            queryset = Notification.objects.filter(complex__board_members=user)
        else:
            # ساکنین فقط اطلاع‌رسانی‌های مربوط به خود را می‌بینند
            user_units = user.owned_units.all() | user.residing_units.all()
            user_complexes = user_units.values_list('building__complex', flat=True)
            queryset = Notification.objects.filter(complex_id__in=user_complexes)
        
        if complex_id:
            queryset = queryset.filter(complex_id=complex_id)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def send_now(self, request, pk=None):
        """ارسال فوری اطلاع‌رسانی"""
        notification = self.get_object()
        
        if notification.is_sent:
            return Response(
                {'error': 'این اطلاع‌رسانی قبلاً ارسال شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # در اینجا کد ارسال واقعی (ایمیل/SMS/پوش) قرار می‌گیرد
        notification.is_sent = True
        notification.sent_at = timezone.now()
        notification.save()
        
        return Response({'message': 'اطلاع‌رسانی با موفقیت ارسال شد'})

class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        complex_id = self.request.query_params.get('complex_id')
        
        if user.user_type in ['manager', 'board_member']:
            queryset = Meeting.objects.filter(complex__board_members=user)
        else:
            # ساکنین فقط جلسات عمومی را می‌بینند
            user_units = user.owned_units.all() | user.residing_units.all()
            user_complexes = user_units.values_list('building__complex', flat=True)
            queryset = Meeting.objects.filter(
                complex_id__in=user_complexes,
                meeting_type__in=['general', 'emergency']
            )
        
        if complex_id:
            queryset = queryset.filter(complex_id=complex_id)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def rsvp(self, request, pk=None):
        """تأیید حضور در جلسه"""
        meeting = self.get_object()
        status = request.data.get('status', 'confirmed')
        
        attendance, created = MeetingAttendance.objects.get_or_create(
            meeting=meeting,
            user=request.user,
            defaults={'status': status, 'responded_at': timezone.now()}
        )
        
        if not created:
            attendance.status = status
            attendance.responded_at = timezone.now()
            attendance.save()
        
        return Response({'message': 'وضعیت حضور شما ثبت شد'})

class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.filter(is_published=True)
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        complex_id = self.request.query_params.get('complex_id')
        
        # فیلتر بر اساس تاریخ انقضا
        queryset = Announcement.objects.filter(
            is_published=True,
            publish_date__lte=timezone.now()
        ).filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gte=timezone.now())
        )
        
        if user.user_type not in ['manager', 'board_member']:
            # ساکنین فقط اطلاعیه‌های مربوط به واحدهای خود را می‌بینند
            user_units = user.owned_units.all() | user.residing_units.all()
            queryset = queryset.filter(
                Q(target_units__isnull=True) | Q(target_units__in=user_units)
            ).distinct()
        
        if complex_id:
            queryset = queryset.filter(complex_id=complex_id)
            
        return queryset

class SupportTicketViewSet(viewsets.ModelViewSet):
    queryset = SupportTicket.objects.all()
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type in ['manager', 'board_member', 'staff']:
            # پرسنل می‌توانند همه تیکت‌ها را ببینند
            return SupportTicket.objects.filter(unit__building__complex__board_members=user)
        else:
            # کاربران فقط تیکت‌های خود را می‌بینند
            return SupportTicket.objects.filter(submitted_by=user)
    
    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_response(self, request, pk=None):
        """افزودن پاسخ به تیکت"""
        ticket = self.get_object()
        message = request.data.get('message')
        is_internal = request.data.get('is_internal', False)
        
        if not message:
            return Response(
                {'error': 'پیام پاسخ الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        response = TicketResponse.objects.create(
            ticket=ticket,
            responded_by=request.user,
            message=message,
            is_internal=is_internal
        )
        
        # اگر پاسخ توسط پرسنل است، وضعیت تیکت را به "در دست بررسی" تغییر بده
        if request.user.user_type in ['manager', 'staff'] and ticket.status == 'open':
            ticket.status = 'in_progress'
            ticket.assigned_to = request.user
            ticket.assigned_at = timezone.now()
            ticket.save()
        
        return Response({'message': 'پاسخ با موفقیت اضافه شد'})
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """حل کردن تیکت"""
        ticket = self.get_object()
        
        if ticket.status == 'resolved':
            return Response(
                {'error': 'این تیکت قبلاً حل شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ticket.status = 'resolved'
        ticket.resolved_at = timezone.now()
        ticket.save()
        
        return Response({'message': 'تیکت به عنوان حل شده علامت گذاری شد'})

class TicketResponseViewSet(viewsets.ModelViewSet):
    queryset = TicketResponse.objects.all()
    serializer_class = TicketResponseSerializer
    permission_classes = [IsAuthenticated]

class MeetingMinuteViewSet(viewsets.ModelViewSet):
    queryset = MeetingMinute.objects.all()
    serializer_class = MeetingMinuteSerializer
    permission_classes = [IsAuthenticated]

class MeetingAttendanceViewSet(viewsets.ModelViewSet):
    queryset = MeetingAttendance.objects.all()
    serializer_class = MeetingAttendanceSerializer
    permission_classes = [IsAuthenticated]