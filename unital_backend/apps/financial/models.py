from django.db import models
from django.core.validators import MinValueValidator
from apps.accounts.models import User
from apps.complexes.models import Unit, Building

class ChargeTemplate(models.Model):
    CHARGE_TYPES = (
        ('monthly', 'شارژ ماهیانه'),
        ('building_maintenance', 'هزینه نگهداری ساختمان'),
        ('elevator', 'آسانسور'),
        ('cleaner', 'نظافت'),
        ('security', 'حفاظت'),
        ('green_space', 'فضای سبز'),
        ('pool', 'استخر'),
        ('gym', 'باشگاه'),
        ('other', 'سایر'),
    )
    
    complex = models.ForeignKey(
        Building, 
        on_delete=models.CASCADE, 
        related_name='charge_templates',
        verbose_name='مجتمع'
    )
    name = models.CharField(max_length=100, verbose_name='نام هزینه')
    charge_type = models.CharField(max_length=50, choices=CHARGE_TYPES, verbose_name='نوع هزینه')
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ'
    )
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'الگوی شارژ'
        verbose_name_plural = 'الگوهای شارژ'
        unique_together = ['complex', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.complex.name}"

class Charge(models.Model):
    STATUS_CHOICES = (
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('overdue', 'معوقه'),
        ('cancelled', 'لغو شده'),
        ('partially_paid', 'پرداخت جزئی'),
    )
    
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        related_name='charges',
        verbose_name='واحد'
    )
    template = models.ForeignKey(
        ChargeTemplate, 
        on_delete=models.CASCADE, 
        verbose_name='الگوی شارژ'
    )
    period = models.CharField(max_length=7, verbose_name='دوره')  # YYYY-MM
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ'
    )
    due_date = models.DateField(verbose_name='تاریخ سررسید')
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='وضعیت'
    )
    
    # محاسبات
    paid_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ پرداخت شده'
    )
    remaining_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ باقیمانده'
    )
    
    # جزئیات
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        verbose_name='ایجاد کننده'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'شارژ'
        verbose_name_plural = 'شارژها'
        unique_together = ['unit', 'template', 'period']
        ordering = ['-due_date', 'unit']
    
    def __str__(self):
        return f"{self.unit} - {self.template.name} - {self.period}"
    
    def save(self, *args, **kwargs):
        if not self.remaining_amount:
            self.remaining_amount = self.amount - self.paid_amount
        super().save(*args, **kwargs)

class Transaction(models.Model):
    PAYMENT_METHODS = (
        ('online', 'آنلاین'),
        ('cash', 'نقدی'),
        ('bank_transfer', 'کارت به کارت'),
        ('cheque', 'چک'),
        ('pos', 'دستگاه پوز'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'در انتظار'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
        ('cancelled', 'لغو شده'),
    )
    
    charge = models.ForeignKey(
        Charge, 
        on_delete=models.CASCADE, 
        related_name='transactions',
        verbose_name='شارژ مربوطه'
    )
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ تراکنش'
    )
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHODS, 
        verbose_name='روش پرداخت'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='وضعیت تراکنش'
    )
    
    # اطلاعات پرداخت
    reference_id = models.CharField(
        max_length=100, 
        unique=True, 
        blank=True, 
        null=True,
        verbose_name='شماره پیگیری'
    )
    payment_date = models.DateTimeField(blank=True, null=True, verbose_name='تاریخ پرداخت')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'تراکنش'
        verbose_name_plural = 'تراکنش‌ها'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.charge.unit} - {self.amount} - {self.get_status_display()}"

class Invoice(models.Model):
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        related_name='invoices',
        verbose_name='واحد'
    )
    period = models.CharField(max_length=7, verbose_name='دوره')  # YYYY-MM
    total_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ کل'
    )
    paid_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ پرداخت شده'
    )
    remaining_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ باقیمانده'
    )
    
    # وضعیت
    is_paid = models.BooleanField(default=False, verbose_name='پرداخت شده')
    due_date = models.DateField(verbose_name='تاریخ سررسید')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'فاکتور'
        verbose_name_plural = 'فاکتورها'
        unique_together = ['unit', 'period']
        ordering = ['-period', 'unit']
    
    def __str__(self):
        return f"{self.unit} - {self.period} - {self.total_amount}"