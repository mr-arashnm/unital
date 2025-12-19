from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .permissions import IsTicketParticipantOrStaff
from django.db.models import Q
from django.utils import timezone
from .models import (
    Notification, Meeting, MeetingAttendance, MeetingMinute,
    Announcement, SupportTicket, TicketResponse
)
from .models import Team
from .serializers import (
    NotificationSerializer, MeetingSerializer, MeetingAttendanceSerializer,
    MeetingMinuteSerializer, AnnouncementSerializer, SupportTicketSerializer,
    TicketResponseSerializer, TeamSerializer
)

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsTicketParticipantOrStaff]
    
    def get_queryset(self):
        user = self.request.user
        complex_id = self.request.query_params.get('complex_id')
        # build base complex set for the user (complexes where user has units)
        user_units = user.owned_units.all() | user.residing_units.all()
        user_complexes = list(user_units.values_list('building__complex', flat=True))

        # managers/board members can also see notifications for complexes they manage
        if user.user_type in ['manager', 'board_member']:
            base_q = Notification.objects.filter(complex__board_members=user)
        else:
            base_q = Notification.objects.filter(complex_id__in=user_complexes)

        # filter by complex if provided
        if complex_id:
            base_q = base_q.filter(complex_id=complex_id)

        # now include notifications targeted to user's role(s), teams, or specific user
        from django.db.models import Q
        q = Q()
        # role-based (JSONField contains)
        q |= Q(target_roles__contains=[user.user_type])
        # specific users
        q |= Q(specific_users=user)
        # team-based
        user_teams = Team.objects.filter(members=user)
        if user_teams.exists():
            q |= Q(target_teams__in=user_teams)

        # legacy target_type handling
        if user.user_type == 'owner':
            # owners see owner-targeted messages
            q |= Q(target_type='owners')
        if user.user_type == 'resident':
            q |= Q(target_type='residents')
        if user.user_type in ['manager', 'board_member']:
            q |= Q(target_type='board')
        q |= Q(target_type='all')

        queryset = base_q.filter(q).distinct()
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
        # base complexes for the user
        user_units = user.owned_units.all() | user.residing_units.all()
        user_complexes = list(user_units.values_list('building__complex', flat=True))

        if user.user_type in ['manager', 'board_member']:
            base_q = Meeting.objects.filter(complex__board_members=user)
        else:
            base_q = Meeting.objects.filter(complex_id__in=user_complexes, meeting_type__in=['general', 'emergency'])

        if complex_id:
            base_q = base_q.filter(complex_id=complex_id)

        # further filter by target_roles or target_teams if set
        from django.db.models import Q
        q = Q()
        q |= Q(target_roles__contains=[user.user_type])
        q |= Q(attendees=user)
        user_teams = Team.objects.filter(members=user)
        if user_teams.exists():
            q |= Q(target_teams__in=user_teams)

        # always include meetings targeted to 'all' via meeting_type/general fallback already handled
        queryset = base_q.filter(q).distinct()
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
        base_q = Announcement.objects.filter(
            is_published=True,
            publish_date__lte=timezone.now()
        ).filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gte=timezone.now())
        )

        # base complexes where user has units
        user_units = user.owned_units.all() | user.residing_units.all()
        user_complexes = list(user_units.values_list('building__complex', flat=True))

        if user.user_type in ['manager', 'board_member']:
            base_q = base_q.filter(complex__board_members=user)
        else:
            base_q = base_q.filter(complex_id__in=user_complexes)

        if complex_id:
            base_q = base_q.filter(complex_id=complex_id)

        from django.db.models import Q
        q = Q()
        q |= Q(target_roles__contains=[user.user_type])
        user_teams = Team.objects.filter(members=user)
        if user_teams.exists():
            q |= Q(target_teams__in=user_teams)
        # units targeting
        q |= Q(target_units__isnull=True) | Q(target_units__in=user_units)

        queryset = base_q.filter(q).distinct()
        return queryset

class SupportTicketViewSet(viewsets.ModelViewSet):
    queryset = SupportTicket.objects.all()
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # start with tickets that belong to buildings which have the 'support_tickets' feature
        base_q = SupportTicket.objects.filter(unit__building__features__key='support_tickets')

        # users in admin roles see complex tickets
        if user.user_type in ['manager', 'board_member', 'staff']:
            return base_q.filter(unit__building__complex__board_members=user)

        # team members see tickets assigned to their team
        user_teams = Team.objects.filter(members=user)
        if user_teams.exists():
            return base_q.filter(Q(team__in=user_teams) | Q(submitted_by=user)).distinct()

        # default: user sees their own tickets (but only for buildings that have the feature)
        return base_q.filter(submitted_by=user)
    
    def perform_create(self, serializer):
        # allow creating tickets associated with a team (optional)
        team_id = self.request.data.get('team')
        if team_id:
            try:
                team = Team.objects.get(id=team_id)
            except Team.DoesNotExist:
                team = None
        else:
            team = None
        # ensure the unit's building supports support_tickets
        unit = serializer.validated_data.get('unit')
        if unit is None:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'unit': 'Unit is required'})

        if not unit.building.has_feature('support_tickets'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('This building does not enable support tickets')

        serializer.save(submitted_by=self.request.user, team=team)
    
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

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    # lightweight serializer using only name and members will be used by admin/frontends
    # We will reuse UserInfoSerializer to show member info via nested serializers if needed
    # For now expose simple fields via ModelSerializer by DRF default behavior
    permission_classes = [IsAuthenticated]

class MeetingMinuteViewSet(viewsets.ModelViewSet):
    queryset = MeetingMinute.objects.all()
    serializer_class = MeetingMinuteSerializer
    permission_classes = [IsAuthenticated]

class MeetingAttendanceViewSet(viewsets.ModelViewSet):
    queryset = MeetingAttendance.objects.all()
    serializer_class = MeetingAttendanceSerializer
    permission_classes = [IsAuthenticated]