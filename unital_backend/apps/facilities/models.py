from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import User
from apps.complexes.models import Complex, Unit
from decimal import Decimal

class Facility(models.Model):
    FACILITY_TYPES = (
        ('pool', 'استخر'),
        ('gym', 'باشگاه ورزشی'),
        ('roof_garden', 'روف گاردن'),
        ('meeting_room', 'سالن اجتماعات'),
        ('party_hall', 'سالن جشن'),
        ('guest_parking', 'پارکینگ مهمان'),
        ('playground', 'زمین بازی'),
        ('sports_court', 'زمین ورزشی'),
        ('library', 'کتابخانه'),
        ('business_center', 'مرکز کسب و کار'),
        ('other', 'سایر'),
    )
    
    complex = models.ForeignKey(
        Complex, 
        on_delete=models.CASCADE, 
        related_name='facilities',
        verbose_name='مجتمع'
    )
    name = models.CharField(max_length=100, verbose_name='نام مکان')
    facility_type = models.CharField(max_length=20, choices=FACILITY_TYPES, verbose_name='نوع مکان')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    
    # ظرفیت و محدودیت‌ها
    capacity = models.PositiveIntegerField(verbose_name='ظرفیت')
    min_advance_booking = models.PositiveIntegerField(
        default=1,
        verbose_name='حداقل زمان رزرو قبلی (ساعت)'
    )
    max_advance_booking = models.PositiveIntegerField(
        default=168,
        verbose_name='حداکثر زمان رزرو قبلی (ساعت)'
    )
    
    # ساعات کاری
    opening_time = models.TimeField(verbose_name='ساعت شروع')
    closing_time = models.TimeField(verbose_name='ساعت پایان')
    
    # قوانین و هزینه
    rules = models.TextField(blank=True, null=True, verbose_name='قوانین استفاده')
    hourly_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        default=0,
        verbose_name='هزینه ساعتی'
    )
    is_free = models.BooleanField(default=True, verbose_name='رایگان')
    
    # وضعیت
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    under_maintenance = models.BooleanField(default=False, verbose_name='در دست تعمیر')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'امکان عمومی'
        verbose_name_plural = 'امکانات عمومی'
        ordering = ['complex', 'facility_type']
    
    def __str__(self):
        return f"{self.name} - {self.complex.name}"

class FacilityBooking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'در انتظار تأیید'),
        ('confirmed', 'تأیید شده'),
        ('active', 'در حال استفاده'),
        ('completed', 'پایان یافته'),
        ('cancelled', 'لغو شده'),
        ('rejected', 'رد شده'),
    )
    
    facility = models.ForeignKey(
        Facility, 
        on_delete=models.CASCADE, 
        related_name='bookings',
        verbose_name='امکان'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='facility_bookings',
        verbose_name='کاربر'
    )
    
    # زمان‌بندی
    start_time = models.DateTimeField(verbose_name='زمان شروع')
    end_time = models.DateTimeField(verbose_name='زمان پایان')
    duration_hours = models.PositiveIntegerField(verbose_name='مدت زمان (ساعت)')
    
    # اطلاعات رزرو
    purpose = models.CharField(max_length=200, verbose_name='هدف استفاده')
    participants_count = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='تعداد شرکت‌کنندگان'
    )
    special_requirements = models.TextField(blank=True, null=True, verbose_name='نیازهای ویژه')
    
    # وضعیت و تأیید
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت')
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_bookings',
        limit_choices_to={'user_type__in': ['manager', 'staff']},
        verbose_name='تأیید کننده'
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان تأیید')
    
    # هزینه
    total_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        default=0,
        verbose_name='هزینه کل'
    )
    is_paid = models.BooleanField(default=False, verbose_name='پرداخت شده')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'رزرو امکان'
        verbose_name_plural = 'رزرو امکانات'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.facility.name} - {self.user} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # محاسبه خودکار مدت زمان
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            # ensure an integer number of hours (use floor)
            self.duration_hours = int(duration.total_seconds() // 3600)
        
        # محاسبه هزینه
        if not self.facility.is_free:
            # use Decimal for monetary calculation
            self.total_cost = Decimal(self.duration_hours) * Decimal(self.facility.hourly_rate)
        
        super().save(*args, **kwargs)

class FacilityMaintenance(models.Model):
    MAINTENANCE_TYPES = (
        ('routine', 'روتین'),
        ('repair', 'تعمیر'),
        ('cleaning', 'نظافت'),
        ('inspection', 'بازرسی'),
        ('upgrade', 'ارتقا'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'کم'),
        ('medium', 'متوسط'),
        ('high', 'بالا'),
        ('urgent', 'فوری'),
    )
    
    facility = models.ForeignKey(
        Facility, 
        on_delete=models.CASCADE, 
        related_name='maintenances',
        verbose_name='امکان'
    )
    title = models.CharField(max_length=200, verbose_name='عنوان')
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES, verbose_name='نوع نگهداری')
    description = models.TextField(verbose_name='توضیحات')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='اولویت')
    
    # زمان‌بندی
    scheduled_start = models.DateTimeField(verbose_name='زمان شروع برنامه‌ریزی شده')
    scheduled_end = models.DateTimeField(verbose_name='زمان پایان برنامه‌ریزی شده')
    actual_start = models.DateTimeField(null=True, blank=True, verbose_name='زمان شروع واقعی')
    actual_end = models.DateTimeField(null=True, blank=True, verbose_name='زمان پایان واقعی')
    
    # وضعیت
    status = models.CharField(
        max_length=20, 
        choices=FacilityBooking.STATUS_CHOICES, 
        default='pending',
        verbose_name='وضعیت'
    )
    
    # مسئول
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'user_type': 'staff'},
        related_name='assigned_facility_maintenances',
        verbose_name='مسئول'
    )
    
    # تأثیر بر رزروها
    affect_bookings = models.BooleanField(default=True, verbose_name='تأثیر بر رزروها')
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_facility_maintenances',
        verbose_name='ایجاد کننده'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'نگهداری امکان'
        verbose_name_plural = 'نگهداری امکانات'
        ordering = ['-scheduled_start']
    
    def __str__(self):
        return f"{self.title} - {self.facility.name}"

class FacilityUsageRule(models.Model):
    facility = models.ForeignKey(
        Facility, 
        on_delete=models.CASCADE, 
        related_name='usage_rules',
        verbose_name='امکان'
    )
    rule = models.TextField(verbose_name='قانون')
    is_mandatory = models.BooleanField(default=True, verbose_name='الزامی')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'قانون استفاده'
        verbose_name_plural = 'قوانین استفاده'
    
    def __str__(self):
        return f"{self.facility.name} - {self.rule[:50]}..."

class FacilityImage(models.Model):
    facility = models.ForeignKey(
        Facility, 
        on_delete=models.CASCADE, 
        related_name='images',
        verbose_name='امکان'
    )
    image = models.ImageField(upload_to='facility_images/', verbose_name='تصویر')
    caption = models.CharField(max_length=200, blank=True, null=True, verbose_name='عنوان')
    is_primary = models.BooleanField(default=False, verbose_name='تصویر اصلی')
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'تصویر امکان'
        verbose_name_plural = 'تصاویر امکانات'
    
    def __str__(self):
        return f"{self.facility.name} - {self.caption or 'Image'}"