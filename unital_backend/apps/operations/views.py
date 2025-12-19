from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Q, F, ExpressionWrapper, DurationField
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from .models import Team, Task, ServiceRequest, TaskComment, Performance
from .serializers import (
    TeamSerializer, TaskSerializer, ServiceRequestSerializer,
    TaskCommentSerializer, PerformanceSerializer
)

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.filter(is_active=True)
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['manager', 'board_member', 'staff']:
            return Team.objects.filter(complex__board_members=user)
        return Team.objects.none()
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """اضافه کردن عضو به تیم"""
        team = self.get_object()
        member_id = request.data.get('member_id')
        # only managers/board_members or staff supervisors may add members
        if request.user.user_type not in ['manager', 'board_member', 'staff']:
            return Response({'error': 'دسترسی غیرمجاز'}, status=status.HTTP_403_FORBIDDEN)

        try:
            from apps.accounts.models import User
            member = User.objects.get(id=member_id, user_type='staff')
            team.members.add(member)
            return Response({'message': 'عضو با موفقیت اضافه شد'})
        except User.DoesNotExist:
            return Response({'error': 'کاربر یافت نشد یا نوع کاربری نامعتبر است'}, status=status.HTTP_400_BAD_REQUEST)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['manager', 'board_member']:
            return Task.objects.filter(team__complex__board_members=user)
        elif user.user_type == 'staff':
            return Task.objects.filter(
                Q(assigned_to=user) | Q(team__supervisor=user) | Q(team__members=user)
            ).distinct()
        return Task.objects.none()
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """تخصیص وظیفه به کارمند"""
        task = self.get_object()
        staff_id = request.data.get('staff_id')
        # only managers/board_members or team supervisors can assign
        if request.user.user_type not in ['manager', 'board_member', 'staff']:
            return Response({'error': 'دسترسی غیرمجاز'}, status=status.HTTP_403_FORBIDDEN)

        try:
            from apps.accounts.models import User
            staff = User.objects.get(id=staff_id, user_type='staff')

            task.assigned_to = staff
            task.status = 'assigned'
            task.assigned_at = timezone.now()
            task.save()

            return Response({'message': 'وظیفه با موفقیت تخصیص داده شد'})
        except User.DoesNotExist:
            return Response({'error': 'کارمند یافت نشد'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """شروع انجام وظیفه"""
        task = self.get_object()
        
        if task.status not in ['assigned', 'pending']:
            return Response(
                {'error': 'وظیفه قابل شروع نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.status = 'in_progress'
        task.started_at = timezone.now()
        task.save()
        
        return Response({'message': 'وظیفه شروع شد'})
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """تکمیل وظیفه"""
        task = self.get_object()
        actual_hours = request.data.get('actual_hours')
        
        if task.status != 'in_progress':
            return Response(
                {'error': 'وظیفه در حال انجام نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.status = 'completed'
        task.completed_at = timezone.now()
        if actual_hours:
            task.actual_hours = actual_hours
        task.save()
        
        return Response({'message': 'وظیفه تکمیل شد'})

class ServiceRequestViewSet(viewsets.ModelViewSet):
    queryset = ServiceRequest.objects.all()
    serializer_class = ServiceRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['manager', 'board_member', 'staff']:
            return ServiceRequest.objects.filter(unit__building__complex__board_members=user)
        elif user.user_type in ['resident', 'owner']:
            return ServiceRequest.objects.filter(submitted_by=user)
        return ServiceRequest.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def assign_to_team(self, request, pk=None):
        """تخصیص درخواست به تیم"""
        service_request = self.get_object()
        team_id = request.data.get('team_id')
        # only managers or staff can assign requests to teams
        if request.user.user_type not in ['manager', 'board_member', 'staff']:
            return Response({'error': 'دسترسی غیرمجاز'}, status=status.HTTP_403_FORBIDDEN)

        try:
            team = Team.objects.get(id=team_id)

            # Atomic: create task and update service request together
            with transaction.atomic():
                service_request.assigned_team = team
                service_request.status = 'assigned'
                service_request.assigned_at = timezone.now()
                service_request.save()

                # ایجاد وظیفه مرتبط
                task = Task.objects.create(
                    title=f"درخواست: {service_request.title}",
                    description=service_request.description,
                    team=team,
                    priority=service_request.priority,
                    related_unit=service_request.unit,
                    due_date=timezone.now() + timedelta(days=3),  # 3 روز مهلت
                    created_by=request.user
                )

                service_request.related_task = task
                service_request.save()

            return Response({'message': 'درخواست به تیم تخصیص داده شد'})
        except Team.DoesNotExist:
            return Response({'error': 'تیم یافت نشد'}, status=status.HTTP_400_BAD_REQUEST)

class TaskCommentViewSet(viewsets.ModelViewSet):
    queryset = TaskComment.objects.all()
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = Performance.objects.all()
    serializer_class = PerformanceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['manager', 'board_member']:
            return Performance.objects.filter(team__complex__board_members=user)
        return Performance.objects.none()
    
    @action(detail=False, methods=['get'])
    def team_performance(self, request):
        """گزارش عملکرد تیم‌ها"""
        complex_id = request.query_params.get('complex_id')
        period = request.query_params.get('period')
        
        teams = Team.objects.filter(complex_id=complex_id)
        performance_data = []
        
        for team in teams:
            tasks = Task.objects.filter(team=team)
            if period:
                tasks = tasks.filter(created_at__startswith=period)
            
            total_tasks = tasks.count()
            completed_tasks = tasks.filter(status='completed').count()
            overdue_tasks = tasks.filter(
                status__in=['assigned', 'in_progress'],
                due_date__lt=timezone.now()
            ).count()
            
            completed_tasks_with_time = tasks.filter(
                status='completed',
                started_at__isnull=False,
                completed_at__isnull=False
            )
            
            avg_completion_time = completed_tasks_with_time.aggregate(
                avg_time=Avg(
                    ExpressionWrapper(
                        F('completed_at') - F('started_at'),
                        output_field=DurationField()
                    )
                )
            )['avg_time']
            
            if avg_completion_time:
                avg_hours = avg_completion_time.total_seconds() / 3600
            else:
                avg_hours = 0
            
            performance_data.append({
                'team_id': team.id,
                'team_name': team.name,
                'team_type': team.get_team_type_display(),
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'overdue_tasks': overdue_tasks,
                'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                'average_completion_time': round(avg_hours, 2)
            })
        
        return Response(performance_data)