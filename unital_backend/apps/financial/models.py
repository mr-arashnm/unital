from django.db import models
from django.core.validators import MinValueValidator
from apps.accounts.models import User
from apps.complexes.models import Unit, Building

class ChargeTemplate(models.Model):
    CHARGE_TYPES = (
        ('monthly', 'Monthly charge'),
        ('building_maintenance', 'Building maintenance'),
        ('elevator', 'Elevator'),
        ('cleaner', 'Cleaning'),
        ('security', 'Security'),
        ('green_space', 'Green space'),
        ('pool', 'Pool'),
        ('gym', 'Gym'),
        ('other', 'Other'),
    )
    
    complex = models.ForeignKey(
        Building, 
        on_delete=models.CASCADE, 
        related_name='charge_templates',
        verbose_name='Complex'
    )
    name = models.CharField(max_length=100, verbose_name='Name')
    charge_type = models.CharField(max_length=50, choices=CHARGE_TYPES, verbose_name='Charge type')
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        validators=[MinValueValidator(0)],
        verbose_name='Amount'
    )
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    is_active = models.BooleanField(default=True, verbose_name='Is active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Charge template'
        verbose_name_plural = 'Charge templates'
        unique_together = ['complex', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.complex.name}"

class Charge(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending payment'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
        ('partially_paid', 'Partially paid'),
    )
    
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        related_name='charges',
        verbose_name='Unit'
    )
    template = models.ForeignKey(
        ChargeTemplate, 
        on_delete=models.CASCADE, 
        verbose_name='Template'
    )
    period = models.CharField(max_length=7, verbose_name='دوره')  # YYYY-MM
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        validators=[MinValueValidator(0)],
        verbose_name='Amount'
    )
    due_date = models.DateField(verbose_name='تاریخ سررسید')
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='Status'
    )
    
    # Calculations
    paid_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Paid amount'
    )
    remaining_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Remaining amount'
    )
    
    # Details
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        verbose_name='Created by'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Charge'
        verbose_name_plural = 'Charges'
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
        ('online', 'Online'),
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank transfer'),
        ('cheque', 'Cheque'),
        ('pos', 'POS'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    charge = models.ForeignKey(
        Charge, 
        on_delete=models.CASCADE, 
        related_name='transactions',
        verbose_name='Related charge'
    )
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        validators=[MinValueValidator(0)],
        verbose_name='Transaction amount'
    )
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHODS, 
        verbose_name='Payment method'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='Transaction status'
    )
    
    # Payment information
    reference_id = models.CharField(
        max_length=100, 
        unique=True, 
        blank=True, 
        null=True,
        verbose_name='Reference ID'
    )
    payment_date = models.DateTimeField(blank=True, null=True, verbose_name='Payment date')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.charge.unit} - {self.amount} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # ensure a unique reference id is present for external reconciliation
        if not self.reference_id:
            import uuid
            # simple UUID4-based ref (trimmed) to keep it short
            self.reference_id = f"TX-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

class Invoice(models.Model):
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        related_name='invoices',
        verbose_name='Unit'
    )
    period = models.CharField(max_length=7, verbose_name='دوره')  # YYYY-MM
    total_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        validators=[MinValueValidator(0)],
        verbose_name='Total amount'
    )
    paid_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Paid amount'
    )
    remaining_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Remaining amount'
    )
    
    # Status
    is_paid = models.BooleanField(default=False, verbose_name='Is paid')
    due_date = models.DateField(verbose_name='Due date')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        unique_together = ['unit', 'period']
        ordering = ['-period', 'unit']
    
    def __str__(self):
        return f"{self.unit} - {self.period} - {self.total_amount}"