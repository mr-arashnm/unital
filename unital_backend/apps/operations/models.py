from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import User
from apps.complexes.models import Building, Unit

class Team(models.Model):
    TEAM_TYPES = (
        ('security', 'حفاظت'),
        ('maintenance', 'تاسیسات'),
        ('cleaning', 'نظافت'),
        ('landscaping', 'فضای سبز'),
        ('pool', 'استخر'),
        ('gym', 'باشگاه'),
        ('other', 'سایر'),
    )
    
    complex = models.ForeignKey(
        Building, 
        on_delete=models.CASCADE, 
        related_name='teams',
        verbose_name='مجتمع'
    )
    name = models.CharField(max_length=100, verbose_name='نام تیم')
    team_type = models.CharField(max_length=20, choices=TEAM_TYPES, verbose_name='نوع تیم')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    
    # مسئول تیم
    supervisor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        limit_choices_to={'user_type': 'staff'},
        related_name='supervised_teams',
        verbose_name='سرپرست'
    )
    
    # اعضای تیم
    members = models.ManyToManyField(
        User, 
        related_name='team_memberships',
        limit_choices_to={'user_type': 'staff'},
        blank=True,
        verbose_name='اعضا'
    )
    
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'تیم'
        verbose_name_plural = 'تیم‌ها'
        ordering = ['complex', 'team_type']
    
    def __str__(self):
        return f"{self.name} - {self.complex.name}"
    
    @property
    def member_count(self):
        return self.members.count()

class Task(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'کم'),
        ('medium', 'متوسط'),
        ('high', 'بالا'),
        ('urgent', 'فوری'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'در انتظار'),
        ('assigned', 'تخصیص داده شده'),
        ('in_progress', 'در حال انجام'),
        ('completed', 'انجام شده'),
        ('cancelled', 'لغو شده'),
        ('on_hold', 'متوقف شده'),
    )
    
    title = models.CharField(max_length=200, verbose_name='عنوان وظیفه')
    description = models.TextField(verbose_name='توضیحات')
    
    # تیم و فرد مسئول
    team = models.ForeignKey(
        Team, 
        on_delete=models.CASCADE, 
        related_name='tasks',
        verbose_name='تیم'
    )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        limit_choices_to={'user_type': 'staff'},
        related_name='assigned_tasks',
        verbose_name='واگذار شده به'
    )
    
    # اولویت و وضعیت
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='اولویت')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت')
    
    # زمان‌بندی
    due_date = models.DateTimeField(verbose_name='تاریخ سررسید')
    estimated_hours = models.PositiveIntegerField(
        blank=True, 
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(24)],
        verbose_name='زمان تخمینی (ساعت)'
    )
    actual_hours = models.PositiveIntegerField(
        blank=True, 
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(24)],
        verbose_name='زمان واقعی (ساعت)'
    )
    
    # واحد مربوطه (اگر مربوط به واحد خاصی باشد)
    related_unit = models.ForeignKey(
        Unit, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='واحد مربوطه'
    )
    
    # ایجاد کننده
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_tasks',
        verbose_name='ایجاد کننده'
    )
    
    # زمان‌ها
    assigned_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان تخصیص')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان شروع')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان تکمیل')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'وظیفه'
        verbose_name_plural = 'وظایف'
        ordering = ['-due_date', 'priority']
    
    def __str__(self):
        return f"{self.title} - {self.team.name}"

class ServiceRequest(models.Model):
    REQUEST_TYPES = (
        ('maintenance', 'تعمیرات'),
        ('cleaning', 'نظافت'),
        ('security', 'امنیتی'),
        ('complaint', 'شکایت'),
        ('suggestion', 'پیشنهاد'),
        ('other', 'سایر'),
    )
    
    STATUS_CHOICES = (
        ('submitted', 'ثبت شده'),
        ('under_review', 'در دست بررسی'),
        ('assigned', 'تخصیص داده شده'),
        ('in_progress', 'در حال انجام'),
        ('completed', 'انجام شده'),
        ('cancelled', 'لغو شده'),
    )
    
    # اطلاعات درخواست
    title = models.CharField(max_length=200, verbose_name='عنوان درخواست')
    description = models.TextField(verbose_name='توضیحات')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES, verbose_name='نوع درخواست')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted', verbose_name='وضعیت')
    
    # کاربر و واحد
    submitted_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='service_requests',
        limit_choices_to={'user_type__in': ['resident', 'owner']},
        verbose_name='ثبت کننده'
    )
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        related_name='service_requests',
        verbose_name='واحد'
    )
    
    # اولویت
    priority = models.CharField(max_length=20, choices=Task.PRIORITY_CHOICES, default='medium', verbose_name='اولویت')
    
    # پیگیری
    assigned_team = models.ForeignKey(
        Team, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='تیم مسئول'
    )
    related_task = models.OneToOneField(
        Task, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='service_request',
        verbose_name='وظیفه مرتبط'
    )
    
    # زمان‌ها
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت')
    assigned_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان تخصیص')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان تکمیل')
    
    class Meta:
        verbose_name = 'درخواست خدمات'
        verbose_name_plural = 'درخواست‌های خدمات'
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
        verbose_name = 'نظر وظیفه'
        verbose_name_plural = 'نظرات وظایف'
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
        verbose_name = 'عملکرد تیم'
        verbose_name_plural = 'عملکرد تیم‌ها'
        unique_together = ['team', 'period']
        ordering = ['-period', 'team']
    
    def __str__(self):
        return f"{self.team.name} - {self.period}"
    
    @property
    def completion_rate(self):
        if self.total_tasks > 0:
            return (self.completed_tasks / self.total_tasks) * 100
        return 0