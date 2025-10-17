from time import timezone
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
    def assigned_storages(self):
        """انباری‌ها و پارکینگ‌های تخصیص داده شده به این واحد"""
        return self.assigned_storages.all()
    
    @property
    def active_storage_assignments(self):
        """تخصیص‌های فعال انباری و پارکینگ"""
        return self.storage_assignments.filter(is_active=True)
    
    def get_storage_by_type(self, storage_type):
        """دریافت انباری/پارکینگ بر اساس نوع"""
        return self.assigned_storages.filter(storage_type=storage_type)
    
    def assign_storage(self, storage_unit, assignment_type, start_date, created_by, **kwargs):
        """تخصیص انباری/پارکینگ به واحد"""
        # بررسی اینکه انباری/پارکینگ خالی باشد
        if not storage_unit.is_available():
            return False, "انباری/پارکینگ در حال حاضر اشغال شده است"
        
        # ایجاد تخصیص
        assignment = StorageAssignment.objects.create(
            storage_unit=storage_unit,
            unit=self,
            assignment_type=assignment_type,
            start_date=start_date,
            end_date=kwargs.get('end_date'),
            monthly_fee=kwargs.get('monthly_fee', storage_unit.monthly_fee),
            is_included_in_charge=kwargs.get('is_included_in_charge', True),
            contract_number=kwargs.get('contract_number'),
            description=kwargs.get('description'),
            created_by=created_by
        )
        
        return True, assignment
    
    
    @property
    def full_address(self):
        return f"{self.building.complex.name} - ساختمان {self.building.name} - واحد {self.unit_number}"
    
    def change_ownership(self, new_owner, transfer_date, contract_number=None, recorded_by=None, description=None):
        """تغییر مالکیت واحد و ثبت در تاریخچه"""
        previous_owner = self.owner
        
        # ایجاد رکورد تاریخچه
        UnitTransferHistory.objects.create(
            unit=self,
            transfer_type='ownership',
            previous_owner=previous_owner,
            new_owner=new_owner,
            previous_resident=self.current_resident,  # ساکن تغییر نمی‌کند
            new_resident=self.current_resident,
            transfer_date=transfer_date,
            contract_number=contract_number,
            contract_date=transfer_date,
            description=description,
            recorded_by=recorded_by
        )
        
        # به‌روزرسانی مالک فعلی
        self.owner = new_owner
        self.save()
        
        return True
    
    def change_residency(self, new_resident, transfer_date, description=None, recorded_by=None):
        """تغییر ساکن واحد و ثبت در تاریخچه"""
        previous_resident = self.current_resident
        
        # ایجاد رکورد تاریخچه
        UnitTransferHistory.objects.create(
            unit=self,
            transfer_type='residency',
            previous_owner=self.owner,  # مالک تغییر نمی‌کند
            new_owner=self.owner,
            previous_resident=previous_resident,
            new_resident=new_resident,
            transfer_date=transfer_date,
            description=description,
            recorded_by=recorded_by
        )
        
        # به‌روزرسانی ساکن فعلی
        self.current_resident = new_resident
        self.save()
        
        return True
    
    def get_transfer_history(self):
        """دریافت تاریخچه کامل انتقالات واحد"""
        return self.transfer_history.all()
    
    def get_ownership_history(self):
        """دریافت تاریخچه مالکین"""
        return self.transfer_history.filter(
            transfer_type__in=['ownership', 'both']
        )
    
    def get_residency_history(self):
        """دریافت تاریخچه ساکنین"""
        return self.transfer_history.filter(
            transfer_type__in=['residency', 'both']
        )
    
    
    
class UnitTransferHistory(models.Model):
    TRANSFER_TYPES = (
        ('ownership', 'تغییر مالکیت'),
        ('residency', 'تغییر سکونت'),
        ('both', 'تغییر مالکیت و سکونت'),
    )
    
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        related_name='transfer_history',
        verbose_name='واحد'
    )
    
    transfer_type = models.CharField(
        max_length=20, 
        choices=TRANSFER_TYPES, 
        verbose_name='نوع انتقال'
    )
    
    # مالک/ساکن قبلی
    previous_owner = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='previous_ownerships',
        verbose_name='مالک قبلی'
    )
    previous_resident = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='previous_residencies', 
        verbose_name='ساکن قبلی'
    )
    
    # مالک/ساکن جدید
    new_owner = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='new_ownerships',
        verbose_name='مالک جدید'
    )
    new_resident = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='new_residencies',
        verbose_name='ساکن جدید'
    )
    
    # اطلاعات انتقال
    transfer_date = models.DateField(verbose_name='تاریخ انتقال')
    contract_number = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='شماره قرارداد'
    )
    contract_date = models.DateField(
        blank=True, 
        null=True,
        verbose_name='تاریخ قرارداد'
    )
    description = models.TextField(
        blank=True, 
        null=True,
        verbose_name='توضیحات'
    )
    
    # ثبت کننده
    recorded_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        verbose_name='ثبت کننده'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'تاریخچه انتقال واحد'
        verbose_name_plural = 'تاریخچه انتقالات واحدها'
        ordering = ['-transfer_date', '-created_at']
    
    def __str__(self):
        return f"{self.unit} - {self.get_transfer_type_display()} - {self.transfer_date}"  
    
    
class Contract(models.Model):
    CONTRACT_TYPES = (
        ('purchase', 'قرارداد خرید و فروش'),
        ('rental', 'قرارداد اجاره'),
        ('transfer', 'قرارداد انتقال'),
        ('other', 'سایر قراردادها'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'پیش‌نویس'),
        ('active', 'فعال'),
        ('expired', 'منقضی شده'),
        ('cancelled', 'لغو شده'),
    )
    
    # طرفین قرارداد
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        related_name='contracts',
        verbose_name='واحد'
    )
    contract_type = models.CharField(
        max_length=20, 
        choices=CONTRACT_TYPES, 
        verbose_name='نوع قرارداد'
    )
    
    # طرفین قرارداد
    first_party = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='contracts_as_first_party',
        verbose_name='طرف اول'
    )
    second_party = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='contracts_as_second_party', 
        verbose_name='طرف دوم'
    )
    
    # اطلاعات قرارداد
    contract_number = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name='شماره قرارداد'
    )
    title = models.CharField(max_length=200, verbose_name='عنوان قرارداد')
    description = models.TextField(blank=True, null=True, verbose_name='شرح قرارداد')
    
    # مدت قرارداد
    start_date = models.DateField(verbose_name='تاریخ شروع')
    end_date = models.DateField(blank=True, null=True, verbose_name='تاریخ پایان')
    duration_months = models.PositiveIntegerField(verbose_name='مدت قرارداد (ماه)')
    
    # مالی
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=0, 
        verbose_name='مبلغ قرارداد'
    )
    deposit_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=0, 
        default=0,
        verbose_name='مبلغ ودیعه'
    )
    
    # وضعیت
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        verbose_name='وضعیت'
    )
    
    # فایل‌ها
    contract_file = models.FileField(
        upload_to='contracts/',
        blank=True, 
        null=True,
        verbose_name='فایل قرارداد'
    )
    
    # امضاها
    first_party_signed = models.BooleanField(default=False, verbose_name='امضای طرف اول')
    second_party_signed = models.BooleanField(default=False, verbose_name='امضای طرف دوم')
    signed_date = models.DateField(blank=True, null=True, verbose_name='تاریخ امضا')
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        related_name='created_contracts',
        verbose_name='ایجاد کننده'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'قرارداد'
        verbose_name_plural = 'قراردادها'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.contract_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        # ایجاد خودکار شماره قرارداد
        if not self.contract_number:
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            last_contract = Contract.objects.filter(
                contract_number__startswith=f'CONTRACT-{date_str}'
            ).order_by('-contract_number').first()
            
            if last_contract:
                last_num = int(last_contract.contract_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
                
            self.contract_number = f'CONTRACT-{date_str}-{new_num:04d}'
        
        super().save(*args, **kwargs)
    
    def activate_contract(self):
        """فعال کردن قرارداد و اعمال تغییرات مربوطه"""
        if self.status != 'draft':
            return False
        
        # بر اساس نوع قرارداد، تغییرات لازم را اعمال کن
        if self.contract_type == 'purchase':
            # تغییر مالکیت
            self.unit.owner = self.second_party
            self.unit.save()
            
        elif self.contract_type == 'rental':
            # تغییر ساکن
            self.unit.current_resident = self.second_party
            self.unit.save()
        
        self.status = 'active'
        self.signed_date = timezone.now().date()
        self.save()
        
        return True
    
class StorageUnit(models.Model):
    STORAGE_TYPES = (
        ('storage', 'انباری'),
        ('parking', 'پارکینگ'),
        ('warehouse', 'انبار بزرگ'),
        ('other', 'سایر'),
    )
    
    STATUS_CHOICES = (
        ('available', 'خالی'),
        ('occupied', 'اشغال شده'),
        ('reserved', 'رزرو شده'),
        ('maintenance', 'در دست تعمیر'),
    )
    
    complex = models.ForeignKey(
        Complex, 
        on_delete=models.CASCADE, 
        related_name='storage_units',
        verbose_name='مجتمع'
    )
    
    storage_type = models.CharField(
        max_length=20, 
        choices=STORAGE_TYPES, 
        verbose_name='نوع فضای ذخیره‌سازی'
    )
    
    # اطلاعات شناسایی
    unit_number = models.CharField(max_length=20, verbose_name='شماره انباری/پارکینگ')
    name = models.CharField(max_length=100, verbose_name='نام')
    location = models.CharField(max_length=200, verbose_name='موقعیت')
    
    # مشخصات فنی
    area = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        verbose_name='متراژ (متر مربع)'
    )
    capacity = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='ظرفیت'
    )
    
    # ویژگی‌ها
    features = models.TextField(
        blank=True, 
        null=True,
        verbose_name='ویژگی‌ها'
    )
    is_covered = models.BooleanField(default=False, verbose_name='سرپوشیده')
    has_electricity = models.BooleanField(default=False, verbose_name='دارای برق')
    has_lighting = models.BooleanField(default=True, verbose_name='دارای روشنایی')
    
    # وضعیت
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='available',
        verbose_name='وضعیت'
    )
    
    # مالکیت
    assigned_unit = models.ForeignKey(
        Unit, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_storages',
        verbose_name='واحد مرتبط'
    )
    
    # اطلاعات مالی
    monthly_fee = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=0,
        verbose_name='هزینه ماهیانه'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'انباری/پارکینگ'
        verbose_name_plural = 'انباری‌ها و پارکینگ‌ها'
        unique_together = ['complex', 'unit_number']
        ordering = ['complex', 'storage_type', 'unit_number']
    
    def __str__(self):
        return f"{self.get_storage_type_display()} {self.unit_number} - {self.complex.name}"
    
    @property
    def full_code(self):
        return f"{self.complex.code}-{self.storage_type.upper()}-{self.unit_number}"
    
    def is_available(self):
        return self.status == 'available'

class StorageAssignment(models.Model):
    ASSIGNMENT_TYPES = (
        ('ownership', 'مالکیت'),
        ('rental', 'اجاره'),
        ('temporary', 'موقت'),
        ('shared', 'اشتراکی'),
    )
    
    storage_unit = models.ForeignKey(
        StorageUnit, 
        on_delete=models.CASCADE, 
        related_name='assignments',
        verbose_name='انباری/پارکینگ'
    )
    
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        related_name='storage_assignments',
        verbose_name='واحد'
    )
    
    assignment_type = models.CharField(
        max_length=20, 
        choices=ASSIGNMENT_TYPES, 
        verbose_name='نوع تخصیص'
    )
    
    # مدت تخصیص
    start_date = models.DateField(verbose_name='تاریخ شروع')
    end_date = models.DateField(
        blank=True, 
        null=True,
        verbose_name='تاریخ پایان'
    )
    
    # اطلاعات مالی
    monthly_fee = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=0,
        verbose_name='هزینه ماهیانه'
    )
    is_included_in_charge = models.BooleanField(
        default=True,
        verbose_name='شامل در شارژ'
    )
    
    # وضعیت
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    
    # اطلاعات قرارداد
    contract_number = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='شماره قرارداد'
    )
    description = models.TextField(
        blank=True, 
        null=True,
        verbose_name='توضیحات'
    )
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        verbose_name='ایجاد کننده'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'تخصیص انباری/پارکینگ'
        verbose_name_plural = 'تخصیص‌های انباری و پارکینگ'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.storage_unit} → {self.unit}"
    
    def save(self, *args, **kwargs):
        # اگر تخصیص فعال است، وضعیت انباری/پارکینگ را تغییر بده
        if self.is_active and self.storage_unit.status != 'occupied':
            self.storage_unit.status = 'occupied'
            self.storage_unit.assigned_unit = self.unit
            self.storage_unit.save()
        
        super().save(*args, **kwargs)

class StorageMaintenance(models.Model):
    MAINTENANCE_TYPES = (
        ('cleaning', 'نظافت'),
        ('repair', 'تعمیرات'),
        ('inspection', 'بازرسی'),
        ('painting', 'رنگ‌آمیزی'),
        ('other', 'سایر'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'کم'),
        ('medium', 'متوسط'), 
        ('high', 'بالا'),
        ('urgent', 'فوری'),
    )
    
    storage_unit = models.ForeignKey(
        StorageUnit, 
        on_delete=models.CASCADE, 
        related_name='maintenances',
        verbose_name='انباری/پارکینگ'
    )
    
    title = models.CharField(max_length=200, verbose_name='عنوان')
    maintenance_type = models.CharField(
        max_length=20, 
        choices=MAINTENANCE_TYPES, 
        verbose_name='نوع نگهداری'
    )
    description = models.TextField(verbose_name='توضیحات')
    priority = models.CharField(
        max_length=20, 
        choices=PRIORITY_CHOICES, 
        default='medium',
        verbose_name='اولویت'
    )
    
    # زمان‌بندی
    scheduled_date = models.DateField(verbose_name='تاریخ برنامه‌ریزی شده')
    estimated_duration = models.PositiveIntegerField(
        verbose_name='مدت تخمینی (ساعت)'
    )
    actual_start = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name='زمان شروع واقعی'
    )
    actual_end = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name='زمان پایان واقعی'
    )
    
    # وضعیت
    status = models.CharField(
        max_length=20, 
        choices=StorageUnit.STATUS_CHOICES, 
        default='available',
        verbose_name='وضعیت'
    )
    
    # مسئول
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        limit_choices_to={'user_type': 'staff'},
        related_name='assigned_maintenances',
        verbose_name='مسئول'
    )
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        related_name='created_maintenances',
        verbose_name='ایجاد کننده'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'نگهداری انباری/پارکینگ'
        verbose_name_plural = 'نگهداری انباری‌ها و پارکینگ‌ها'
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.title} - {self.storage_unit}"
    
