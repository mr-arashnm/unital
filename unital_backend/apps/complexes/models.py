from django.db import models
from apps.accounts.models import User

class Complex(models.Model):
    TYPES = (
        ('residential', 'مسکونی'),
        ('commercial', 'تجاری'),
        ('office', 'اداری'),
        ('mixed', 'ترکیبی'),
    )
    
    name = models.CharField(max_length=200, verbose_name='نام مجتمع')
    code = models.CharField(max_length=50, unique=True, verbose_name='کد مجتمع')
    type = models.CharField(max_length=20, choices=TYPES, verbose_name='نوع مجتمع')
    address = models.TextField(verbose_name='آدرس')
    total_units = models.IntegerField(verbose_name='تعداد کل واحدها')
    total_buildings = models.IntegerField(default=1, verbose_name='تعداد ساختمان‌ها')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    
    # مدیریت
    board_members = models.ManyToManyField(
        User, 
        related_name='managed_complexes',
        limit_choices_to={'user_type__in': ['manager', 'board_member']},
        verbose_name='اعضای هیئت مدیره'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_complexes',
        verbose_name='ایجاد کننده'
    )
    
    # زمان‌ها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'مجتمع'
        verbose_name_plural = 'مجتمع‌ها'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Building(models.Model):
    complex = models.ForeignKey(
        Complex, 
        on_delete=models.CASCADE, 
        related_name='buildings',
        verbose_name='مجتمع'
    )
    name = models.CharField(max_length=100, verbose_name='نام ساختمان')
    number = models.CharField(max_length=10, verbose_name='شماره ساختمان')
    floors = models.IntegerField(verbose_name='تعداد طبقات')
    units_per_floor = models.IntegerField(verbose_name='واحد در هر طبقه')
    
    class Meta:
        verbose_name = 'ساختمان'
        verbose_name_plural = 'ساختمان‌ها'
        unique_together = ['complex', 'number']
    
    def __str__(self):
        return f"{self.name} - {self.complex.name}"

class Unit(models.Model):
    UNIT_STATUS = (
        ('occupied', 'ساکن دارد'),
        ('vacant', 'خالی'),
        ('under_construction', 'در دست ساخت'),
        ('reserved', 'رزرو شده'),
    )
    
    building = models.ForeignKey(
        Building, 
        on_delete=models.CASCADE, 
        related_name='units',
        verbose_name='ساختمان'
    )
    unit_number = models.CharField(max_length=20, verbose_name='شماره واحد')
    floor = models.IntegerField(verbose_name='طبقه')
    area = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='متراژ')
    
    # مالک و ساکن فعلی
    owner = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='owned_units',
        limit_choices_to={'user_type__in': ['owner', 'resident']},
        verbose_name='مالک'
    )
    current_resident = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='residing_units', 
        limit_choices_to={'user_type__in': ['resident', 'owner']},
        verbose_name='ساکن فعلی'
    )
    
    status = models.CharField(
        max_length=20, 
        choices=UNIT_STATUS, 
        default='vacant',
        verbose_name='وضعیت'
    )
    
    # اطلاعات اضافی
    rooms = models.IntegerField(default=1, verbose_name='تعداد اتاق')
    parking = models.BooleanField(default=False, verbose_name='پارکینگ')
    storage = models.BooleanField(default=False, verbose_name='انباری')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'واحد'
        verbose_name_plural = 'واحدها'
        unique_together = ['building', 'unit_number']
        ordering = ['building', 'floor', 'unit_number']
    
    def __str__(self):
        return f"واحد {self.unit_number} - {self.building.name}"
    
    @property
    def full_address(self):
        return f"{self.building.complex.name} - ساختمان {self.building.name} - واحد {self.unit_number}"