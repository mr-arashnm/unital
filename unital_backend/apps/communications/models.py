from django.db import models
from apps.accounts.models import User
from apps.complexes.models import Complex, Unit

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('charge', 'شارژ'),
        ('meeting', 'جلسه'),
        ('maintenance', 'تعمیرات'),
        ('security', 'امنیتی'),
        ('general', 'عمومی'),
        ('urgent', 'فوری'),
    )
    
    TARGET_TYPES = (
        ('all', 'همه ساکنین'),
        ('owners', 'مالکین'),
        ('residents', 'ساکنین'),
        ('board', 'هیئت مدیره'),
        ('specific', 'کاربران خاص'),
    )
    
    title = models.CharField(max_length=200, verbose_name='عنوان')
    message = models.TextField(verbose_name='پیام')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name='نوع اطلاع‌رسانی')
    target_type = models.CharField(max_length=20, choices=TARGET_TYPES, verbose_name='مخاطبان')
    
    # مخاطبان خاص
    specific_users = models.ManyToManyField(
        User, 
        blank=True,
        verbose_name='کاربران خاص'
    )
    
    # مجتمع مربوطه
    complex = models.ForeignKey(
        Complex, 
        on_delete=models.CASCADE, 
        verbose_name='مجتمع'
    )
    
    # وضعیت ارسال
    is_sent = models.BooleanField(default=False, verbose_name='ارسال شده')
    scheduled_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان برنامه‌ریزی شده')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان ارسال')
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_notifications',
        verbose_name='ایجاد کننده'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'اطلاع‌رسانی'
        verbose_name_plural = 'اطلاع‌رسانی‌ها'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.complex.name}"

class Meeting(models.Model):
    MEETING_TYPES = (
        ('board', 'هیئت مدیره'),
        ('general', 'عمومی'),
        ('committee', 'کمیته'),
        ('emergency', 'فوری'),
    )
    
    STATUS_CHOICES = (
        ('scheduled', 'برنامه‌ریزی شده'),
        ('ongoing', 'در حال برگزاری'),
        ('completed', 'برگزار شده'),
        ('cancelled', 'لغو شده'),
    )
    
    title = models.CharField(max_length=200, verbose_name='عنوان جلسه')
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPES, verbose_name='نوع جلسه')
    description = models.TextField(verbose_name='توضیحات')
    agenda = models.TextField(verbose_name='دستور جلسه')
    
    # زمان و مکان
    scheduled_date = models.DateTimeField(verbose_name='زمان برگزاری')
    location = models.CharField(max_length=200, verbose_name='محل برگزاری')
    duration = models.PositiveIntegerField(default=60, verbose_name='مدت زمان (دقیقه)')
    
    # وضعیت
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name='وضعیت')
    
    # شرکت‌کنندگان
    attendees = models.ManyToManyField(
        User,
        through='MeetingAttendance',
        related_name='meetings_attended',
        verbose_name='شرکت‌کنندگان'
    )
    
    # مجتمع مربوطه
    complex = models.ForeignKey(
        Complex, 
        on_delete=models.CASCADE, 
        verbose_name='مجتمع'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_meetings',
        verbose_name='ایجاد کننده'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'جلسه'
        verbose_name_plural = 'جلسات'
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.title} - {self.scheduled_date.strftime('%Y-%m-%d')}"

class MeetingAttendance(models.Model):
    ATTENDANCE_STATUS = (
        ('invited', 'دعوت شده'),
        ('confirmed', 'تأیید حضور'),
        ('declined', 'عدم حضور'),
        ('attended', 'حاضر شده'),
        ('absent', 'غایب'),
    )
    
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, verbose_name='جلسه')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر')
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS, default='invited', verbose_name='وضعیت حضور')
    
    # زمان‌ها
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان پاسخ')
    actual_attendance = models.BooleanField(null=True, blank=True, verbose_name='حضور فیزیکی')
    
    class Meta:
        verbose_name = 'حضور در جلسه'
        verbose_name_plural = 'حضور در جلسات'
        unique_together = ['meeting', 'user']
    
    def __str__(self):
        return f"{self.user} - {self.meeting.title}"

class MeetingMinute(models.Model):
    meeting = models.OneToOneField(
        Meeting, 
        on_delete=models.CASCADE, 
        related_name='minutes',
        verbose_name='جلسه'
    )
    content = models.TextField(verbose_name='متن صورتجلسه')
    decisions = models.TextField(verbose_name='مصوبات')
    action_items = models.TextField(verbose_name='اقدامات')
    
    # امضا کنندگان
    signed_by = models.ManyToManyField(
        User, 
        related_name='signed_minutes',
        verbose_name='امضا کنندگان'
    )
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        verbose_name='ثبت کننده'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'صورتجلسه'
        verbose_name_plural = 'صورتجلسات'
    
    def __str__(self):
        return f"صورتجلسه {self.meeting.title}"

class Announcement(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'کم'),
        ('normal', 'معمولی'),
        ('high', 'بالا'),
        ('urgent', 'فوری'),
    )
    
    title = models.CharField(max_length=200, verbose_name='عنوان اطلاعیه')
    content = models.TextField(verbose_name='محتوا')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal', verbose_name='اولویت')
    
    # هدف
    complex = models.ForeignKey(
        Complex, 
        on_delete=models.CASCADE, 
        verbose_name='مجتمع'
    )
    target_units = models.ManyToManyField(
        Unit, 
        blank=True,
        verbose_name='واحدهای هدف'
    )
    
    # وضعیت
    is_published = models.BooleanField(default=False, verbose_name='منتشر شده')
    publish_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ انتشار')
    expiry_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ انقضا')
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        verbose_name='ایجاد کننده'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'اطلاعیه'
        verbose_name_plural = 'اطلاعیه‌ها'
        ordering = ['-publish_date', '-priority']
    
    def __str__(self):
        return self.title

class SupportTicket(models.Model):
    TICKET_TYPES = (
        ('technical', 'فنی'),
        ('financial', 'مالی'),
        ('complaint', 'شکایت'),
        ('suggestion', 'پیشنهاد'),
        ('general', 'عمومی'),
    )
    
    STATUS_CHOICES = (
        ('open', 'باز'),
        ('in_progress', 'در دست بررسی'),
        ('resolved', 'حل شده'),
        ('closed', 'بسته شده'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'کم'),
        ('medium', 'متوسط'),
        ('high', 'بالا'),
        ('urgent', 'فوری'),
    )
    
    title = models.CharField(max_length=200, verbose_name='عنوان تیکت')
    description = models.TextField(verbose_name='شرح مشکل')
    ticket_type = models.CharField(max_length=20, choices=TICKET_TYPES, verbose_name='نوع تیکت')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', verbose_name='وضعیت')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='اولویت')
    
    # کاربر و واحد
    submitted_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='support_tickets',
        verbose_name='ثبت کننده'
    )
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        verbose_name='واحد'
    )
    
    # مسئول پیگیری
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        limit_choices_to={'user_type__in': ['manager', 'staff']},
        verbose_name='واگذار شده به'
    )
    
    # زمان‌ها
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت')
    assigned_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان تخصیص')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان حل')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان بسته شدن')
    
    class Meta:
        verbose_name = 'تیکت پشتیبانی'
        verbose_name_plural = 'تیکت‌های پشتیبانی'
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.title} - {self.submitted_by}"

class TicketResponse(models.Model):
    ticket = models.ForeignKey(
        SupportTicket, 
        on_delete=models.CASCADE, 
        related_name='responses',
        verbose_name='تیکت'
    )
    responded_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='پاسخ دهنده'
    )
    message = models.TextField(verbose_name='پیام')
    attachment = models.FileField(
        upload_to='ticket_attachments/', 
        null=True, 
        blank=True,
        verbose_name='فایل ضمیمه'
    )
    is_internal = models.BooleanField(default=False, verbose_name='پاسخ داخلی')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'پاسخ تیکت'
        verbose_name_plural = 'پاسخ‌های تیکت'
        ordering = ['created_at']
    
    def __str__(self):
        return f"پاسخ به {self.ticket.title}"