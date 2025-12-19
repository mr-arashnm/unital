from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import User
from apps.complexes.models import Building, Unit

class Team(models.Model):
    TEAM_TYPES = (
        ('security', 'Security'),
        ('maintenance', 'Maintenance'),
        ('cleaning', 'Cleaning'),
        ('landscaping', 'Landscaping'),
        ('pool', 'Pool'),
        ('gym', 'Gym'),
        ('other', 'Other'),
    )
    
    complex = models.ForeignKey(
        Building, 
        on_delete=models.CASCADE, 
        related_name='teams',
        verbose_name='Complex'
    )
    name = models.CharField(max_length=100, verbose_name='Name')
    team_type = models.CharField(max_length=20, choices=TEAM_TYPES, verbose_name='Team type')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    
    # Team supervisor
    supervisor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        limit_choices_to={'user_type': 'staff'},
        related_name='supervised_teams',
        verbose_name='Supervisor'
    )
    
    # Team members
    members = models.ManyToManyField(
        User, 
        related_name='team_memberships',
        limit_choices_to={'user_type': 'staff'},
        blank=True,
        verbose_name='Members'
    )
    
    is_active = models.BooleanField(default=True, verbose_name='Is active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'
        ordering = ['complex', 'team_type']
    
    def __str__(self):
        return f"{self.name} - {self.complex.name}"
    
    @property
    def member_count(self):
        return self.members.count()

class Task(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On hold'),
    )
    
    title = models.CharField(max_length=200, verbose_name='Title')
    description = models.TextField(verbose_name='Description')
    
    # تیم و فرد مسئول
    team = models.ForeignKey(
        Team, 
        on_delete=models.CASCADE, 
        related_name='tasks',
        verbose_name='Team'
    )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        limit_choices_to={'user_type': 'staff'},
        related_name='assigned_tasks',
        verbose_name='Assigned to'
    )
    
    # اولویت و وضعیت
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='Priority')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Status')
    
    # زمان‌بندی
    due_date = models.DateTimeField(verbose_name='Due date')
    estimated_hours = models.PositiveIntegerField(
        blank=True, 
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(24)],
        verbose_name='Estimated hours (hours)'
    )
    actual_hours = models.PositiveIntegerField(
        blank=True, 
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(24)],
        verbose_name='Actual hours (hours)'
    )
    
    # واحد مربوطه (اگر مربوط به واحد خاصی باشد)
    related_unit = models.ForeignKey(
        Unit, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Related unit'
    )
    
    # ایجاد کننده
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_tasks',
        verbose_name='Created by'
    )
    
    # زمان‌ها
    assigned_at = models.DateTimeField(null=True, blank=True, verbose_name='Assigned at')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='Started at')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Completed at')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-due_date', 'priority']
    
    def __str__(self):
        return f"{self.title} - {self.team.name}"

class ServiceRequest(models.Model):
    REQUEST_TYPES = (
        ('maintenance', 'Maintenance'),
        ('cleaning', 'Cleaning'),
        ('security', 'Security'),
        ('complaint', 'Complaint'),
        ('suggestion', 'Suggestion'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('submitted', 'Submitted'),
        ('under_review', 'Under review'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    # Request information
    title = models.CharField(max_length=200, verbose_name='Title')
    description = models.TextField(verbose_name='Description')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES, verbose_name='Request type')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted', verbose_name='Status')
    
    # کاربر و واحد
    submitted_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='service_requests',
        limit_choices_to={'user_type__in': ['resident', 'owner']},
        verbose_name='Submitted by'
    )
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        related_name='service_requests',
        verbose_name='Unit'
    )
    
    # اولویت
    priority = models.CharField(max_length=20, choices=Task.PRIORITY_CHOICES, default='medium', verbose_name='Priority')
    
    # پیگیری
    assigned_team = models.ForeignKey(
        Team, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Assigned team'
    )
    related_task = models.OneToOneField(
        Task, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='service_request',
        verbose_name='Related task'
    )
    
    # زمان‌ها
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='Submitted at')
    assigned_at = models.DateTimeField(null=True, blank=True, verbose_name='Assigned at')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Completed at')
    
    class Meta:
        verbose_name = 'Service request'
        verbose_name_plural = 'Service requests'
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.title} - {self.unit}"

class TaskComment(models.Model):
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name='وظیفه'
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='نویسنده'
    )
    comment = models.TextField(verbose_name='نظر')
    attachment = models.FileField(
        upload_to='task_attachments/', 
        null=True, 
        blank=True,
        verbose_name='فایل ضمیمه'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Task comment'
        verbose_name_plural = 'Task comments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.author} on {self.task.title}"

class Performance(models.Model):
    team = models.ForeignKey(
        Team, 
        on_delete=models.CASCADE, 
        related_name='performances',
        verbose_name='تیم'
    )
    period = models.CharField(max_length=7, verbose_name='دوره')  # YYYY-MM
    
    # آمار عملکرد
    total_tasks = models.PositiveIntegerField(default=0, verbose_name='تعداد کل وظایف')
    completed_tasks = models.PositiveIntegerField(default=0, verbose_name='وظایف انجام شده')
    overdue_tasks = models.PositiveIntegerField(default=0, verbose_name='وظایف معوقه')
    average_completion_time = models.FloatField(default=0, verbose_name='میانگین زمان تکمیل (ساعت)')
    
    # رضایت
    satisfaction_rate = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='نرخ رضایت (%)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Team performance'
        verbose_name_plural = 'Team performances'
        unique_together = ['team', 'period']
        ordering = ['-period', 'team']
    
    def __str__(self):
        return f"{self.team.name} - {self.period}"
    
    @property
    def completion_rate(self):
        if self.total_tasks > 0:
            return (self.completed_tasks / self.total_tasks) * 100
        return 0