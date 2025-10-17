from django.contrib import admin
from .models import Complex, Building, Contract, StorageAssignment, StorageMaintenance, StorageUnit, Unit, UnitTransferHistory

class BuildingInline(admin.TabularInline):
    model = Building
    extra = 1
    fields = ('name', 'number', 'floors', 'units_per_floor')
    show_change_link = True

class UnitInline(admin.TabularInline):
    model = Unit
    extra = 1
    fields = ('unit_number', 'floor', 'area', 'owner', 'current_resident', 'status')
    show_change_link = True

@admin.register(Complex)
class ComplexAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'type', 'total_units', 'total_buildings', 'created_by', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('name', 'code', 'address')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('اطلاعات پایه', {'fields': ('name', 'code', 'type', 'address')}),
        ('آمار', {'fields': ('total_units', 'total_buildings', 'description')}),
        ('مدیریت', {'fields': ('board_members', 'created_by')}),
        ('تاریخ‌ها', {'fields': ('created_at', 'updated_at')}),
    )
    
    inlines = [BuildingInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('board_members')

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'complex', 'number', 'floors', 'units_per_floor', 'total_units_count')
    list_filter = ('complex',)
    search_fields = ('name', 'complex__name')
    
    inlines = [UnitInline]
    
    def total_units_count(self, obj):
        return obj.units.count()
    total_units_count.short_description = 'تعداد واحدها'

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('unit_number', 'building', 'floor', 'area', 'owner', 'current_resident', 'status', 'created_at')
    list_filter = ('status', 'building__complex', 'floor', 'created_at')
    search_fields = ('unit_number', 'building__name', 'owner__email', 'current_resident__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('اطلاعات واحد', {'fields': ('building', 'unit_number', 'floor', 'area')}),
        ('مالکیت و سکونت', {'fields': ('owner', 'current_resident', 'status')}),
        ('امکانات', {'fields': ('rooms', 'parking', 'storage')}),
        ('تاریخ‌ها', {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('building', 'owner', 'current_resident')
    
    
@admin.register(UnitTransferHistory)
class UnitTransferHistoryAdmin(admin.ModelAdmin):
    list_display = ('unit', 'transfer_type', 'previous_owner', 'new_owner', 'previous_resident', 'new_resident', 'transfer_date', 'recorded_by')
    list_filter = ('transfer_type', 'transfer_date', 'unit__building__complex')
    search_fields = ('unit__unit_number', 'previous_owner__email', 'new_owner__email', 'contract_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('اطلاعات انتقال', {'fields': ('unit', 'transfer_type', 'transfer_date')}),
        ('طرفین انتقال - مالکیت', {'fields': ('previous_owner', 'new_owner')}),
        ('طرفین انتقال - سکونت', {'fields': ('previous_resident', 'new_resident')}),
        ('اطلاعات قرارداد', {'fields': ('contract_number', 'contract_date', 'description')}),
        ('ثبت کننده', {'fields': ('recorded_by',)}),
        ('تاریخ‌ها', {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'unit', 'previous_owner', 'new_owner', 'previous_resident', 'new_resident', 'recorded_by'
        )
        

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'title', 'unit', 'contract_type', 'first_party', 'second_party', 'status', 'start_date', 'amount')
    list_filter = ('contract_type', 'status', 'start_date', 'unit__building__complex')
    search_fields = ('contract_number', 'title', 'unit__unit_number', 'first_party__email', 'second_party__email')
    readonly_fields = ('contract_number', 'created_at', 'updated_at')
    list_editable = ('status',)
    
    fieldsets = (
        ('اطلاعات قرارداد', {'fields': ('contract_number', 'title', 'contract_type', 'description')}),
        ('طرفین قرارداد', {'fields': ('unit', 'first_party', 'second_party')}),
        ('مدت قرارداد', {'fields': ('start_date', 'end_date', 'duration_months')}),
        ('اطلاعات مالی', {'fields': ('amount', 'deposit_amount')}),
        ('وضعیت و امضا', {'fields': ('status', 'first_party_signed', 'second_party_signed', 'signed_date')}),
        ('فایل', {'fields': ('contract_file',)}),
        ('مدیریت', {'fields': ('created_by',)}),
        ('تاریخ‌ها', {'fields': ('created_at', 'updated_at')}),
    )
    
    actions = ['activate_contracts']
    
    def activate_contracts(self, request, queryset):
        """فعال کردن قراردادهای انتخاب شده"""
        for contract in queryset:
            if contract.status == 'draft':
                contract.activate_contract()
        self.message_user(request, f'{queryset.count()} قرارداد فعال شد')
    activate_contracts.short_description = 'فعال کردن قراردادهای انتخاب شده'
    
    
class StorageAssignmentInline(admin.TabularInline):
    model = StorageAssignment
    extra = 0
    fields = ('unit', 'assignment_type', 'start_date', 'is_active', 'monthly_fee')
    readonly_fields = ('created_at',)

class StorageMaintenanceInline(admin.TabularInline):
    model = StorageMaintenance
    extra = 0
    fields = ('title', 'maintenance_type', 'status', 'scheduled_date', 'assigned_to')
    readonly_fields = ('created_at',)

@admin.register(StorageUnit)
class StorageUnitAdmin(admin.ModelAdmin):
    list_display = ('unit_number', 'name', 'complex', 'storage_type', 'area', 'status', 'assigned_unit', 'monthly_fee', 'is_available')
    list_filter = ('storage_type', 'status', 'complex', 'is_covered', 'has_electricity')
    search_fields = ('unit_number', 'name', 'complex__name', 'location')
    list_editable = ('status', 'monthly_fee')
    
    fieldsets = (
        ('اطلاعات پایه', {'fields': ('complex', 'storage_type', 'unit_number', 'name', 'location')}),
        ('مشخصات فنی', {'fields': ('area', 'capacity', 'features')}),
        ('ویژگی‌ها', {'fields': ('is_covered', 'has_electricity', 'has_lighting')}),
        ('وضعیت و مالکیت', {'fields': ('status', 'assigned_unit', 'monthly_fee')}),
        ('تاریخ‌ها', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    inlines = [StorageAssignmentInline, StorageMaintenanceInline]
    
    def is_available(self, obj):
        return obj.is_available()
    is_available.boolean = True
    is_available.short_description = 'خالی'

@admin.register(StorageAssignment)
class StorageAssignmentAdmin(admin.ModelAdmin):
    list_display = ('storage_unit', 'unit', 'assignment_type', 'start_date', 'end_date', 'is_active', 'monthly_fee')
    list_filter = ('assignment_type', 'is_active', 'start_date', 'storage_unit__storage_type')
    search_fields = ('storage_unit__unit_number', 'unit__unit_number', 'contract_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('اطلاعات تخصیص', {'fields': ('storage_unit', 'unit', 'assignment_type')}),
        ('مدت تخصیص', {'fields': ('start_date', 'end_date', 'is_active')}),
        ('اطلاعات مالی', {'fields': ('monthly_fee', 'is_included_in_charge')}),
        ('قرارداد', {'fields': ('contract_number', 'description')}),
        ('مدیریت', {'fields': ('created_by',)}),
        ('تاریخ‌ها', {'fields': ('created_at', 'updated_at')}),
    )

@admin.register(StorageMaintenance)
class StorageMaintenanceAdmin(admin.ModelAdmin):
    list_display = ('storage_unit', 'title', 'maintenance_type', 'priority', 'status', 'scheduled_date', 'assigned_to')
    list_filter = ('maintenance_type', 'priority', 'status', 'scheduled_date')
    search_fields = ('title', 'storage_unit__unit_number', 'description')
    list_editable = ('status', 'priority')
    
    fieldsets = (
        ('اطلاعات نگهداری', {'fields': ('storage_unit', 'title', 'maintenance_type', 'description', 'priority')}),
        ('زمان‌بندی', {'fields': ('scheduled_date', 'estimated_duration', 'actual_start', 'actual_end')}),
        ('وضعیت و مسئول', {'fields': ('status', 'assigned_to')}),
        ('مدیریت', {'fields': ('created_by',)}),
        ('تاریخ‌ها', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')