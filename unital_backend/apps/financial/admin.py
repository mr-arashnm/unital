from django.contrib import admin
from .models import ChargeTemplate, Charge, Transaction, Invoice

@admin.register(ChargeTemplate)
class ChargeTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'complex', 'charge_type', 'amount', 'is_active', 'created_at')
    list_filter = ('charge_type', 'is_active', 'complex', 'created_at')
    search_fields = ('name', 'complex__name')
    list_editable = ('is_active', 'amount')
    
    fieldsets = (
        ('Template information', {'fields': ('complex', 'name', 'charge_type', 'amount')}),
        ('Description', {'fields': ('description', 'is_active')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Charge)
class ChargeAdmin(admin.ModelAdmin):
    list_display = ('unit', 'template', 'period', 'amount', 'status', 'due_date', 'paid_amount', 'remaining_amount')
    list_filter = ('status', 'period', 'template__charge_type', 'due_date')
    search_fields = ('unit__unit_number', 'unit__building__complex__name', 'template__name')
    readonly_fields = ('created_at', 'updated_at', 'remaining_amount')
    
    fieldsets = (
        ('Charge information', {'fields': ('unit', 'template', 'period', 'amount', 'due_date')}),
        ('Payment status', {'fields': ('status', 'paid_amount', 'remaining_amount', 'description')}),
        ('Management', {'fields': ('created_by',)}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('unit', 'template', 'created_by')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('charge', 'amount', 'payment_method', 'status', 'payment_date', 'reference_id')
    list_filter = ('status', 'payment_method', 'payment_date')
    search_fields = ('charge__unit__unit_number', 'reference_id')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Transaction information', {'fields': ('charge', 'amount', 'payment_method', 'status')}),
        ('Payment information', {'fields': ('reference_id', 'payment_date', 'description')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('unit', 'period', 'total_amount', 'paid_amount', 'remaining_amount', 'is_paid', 'due_date')
    list_filter = ('is_paid', 'period', 'due_date')
    search_fields = ('unit__unit_number', 'unit__building__complex__name')
    
    fieldsets = (
        ('Invoice information', {'fields': ('unit', 'period', 'total_amount')}),
        ('Payment status', {'fields': ('paid_amount', 'remaining_amount', 'is_paid', 'due_date')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')