from django.contrib import admin
from django.utils.html import format_html
from .models import Building, Contract, Unit, UnitTransferHistory, Parking, Warehouse

class ParkingInline(admin.TabularInline):
    model = Parking
    extra = 1
    fields = ('code', 'floor', 'status', 'unit', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

class WarehouseInline(admin.TabularInline):
    model = Warehouse
    extra = 1
    fields = ('code', 'floor', 'status', 'area', 'unit', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'type', 'total_units', 'total_parkings', 'total_warehouses', 'created_by', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('name', 'code', 'address')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'code', 'type', 'address')}),
        ('Statistics', {'fields': ('total_floors', 'total_units', 'total_parkings', 'total_warehouses', 'description')}),
        ('Management', {'fields': ('board_members', 'created_by')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('board_members')

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('building', 'floor', 'area', 'owner', 'resident', 'status', 'created_at')
    list_filter = ('status', 'building', 'floor', 'created_at')
    search_fields = ('unit_number', 'building__name', 'owner__email', 'resident__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ParkingInline, WarehouseInline]
    
    fieldsets = (
        ('Unit Information', {'fields': ('building', 'unit_number', 'floor', 'area')}),
        ('Ownership and Residency', {'fields': ('owner', 'resident', 'status')}),
        ('Additional Info', {'fields': ('rooms',)}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('building', 'owner', 'resident')
    
    def has_parking(self, obj):
        return obj.has_parking()
    has_parking.boolean = True
    has_parking.short_description = 'Parking'
    
    def has_warehouse(self, obj):
        return obj.has_warehouse()
    has_warehouse.boolean = True
    has_warehouse.short_description = 'Warehouse'

@admin.register(UnitTransferHistory)
class UnitTransferHistoryAdmin(admin.ModelAdmin):
    list_display = ('unit', 'transfer_type', 'previous_owner', 'new_owner', 'previous_resident', 'new_resident', 'transfer_date', 'recorded_by')
    list_filter = ('transfer_type', 'transfer_date', 'unit__building')
    search_fields = ('unit__unit_number', 'previous_owner__email', 'new_owner__email', 'contract_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Transfer Information', {'fields': ('unit', 'transfer_type', 'transfer_date')}),
        ('Ownership Transfer', {'fields': ('previous_owner', 'new_owner')}),
        ('Residency Transfer', {'fields': ('previous_resident', 'new_resident')}),
        ('Contract Information', {'fields': ('contract_number', 'contract_date', 'description')}),
        ('Recorded By', {'fields': ('recorded_by',)}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'unit', 'previous_owner', 'new_owner', 'previous_resident', 'new_resident', 'recorded_by'
        )

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'title', 'unit', 'contract_type', 'first_party', 'second_party', 'status', 'start_date', 'amount')
    list_filter = ('contract_type', 'status', 'start_date', 'unit__building')
    search_fields = ('contract_number', 'title', 'unit__unit_number', 'first_party__email', 'second_party__email')
    readonly_fields = ('contract_number', 'created_at', 'updated_at')
    list_editable = ('status',)
    
    fieldsets = (
        ('Contract Information', {'fields': ('contract_number', 'title', 'contract_type', 'description')}),
        ('Contract Parties', {'fields': ('unit', 'first_party', 'second_party')}),
        ('Contract Duration', {'fields': ('start_date', 'end_date', 'duration_months')}),
        ('Financial Information', {'fields': ('amount', 'deposit_amount')}),
        ('Status and Signature', {'fields': ('status', 'first_party_signed', 'second_party_signed', 'signed_date')}),
        ('File', {'fields': ('contract_file',)}),
        ('Management', {'fields': ('created_by',)}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    actions = ['activate_contracts']
    
    def activate_contracts(self, request, queryset):
        """Activate selected contracts"""
        activated_count = 0
        for contract in queryset:
            if contract.status == 'draft':
                success, message = contract.activate_contract()
                if success:
                    activated_count += 1
        self.message_user(request, f'{activated_count} contracts activated successfully')
    activate_contracts.short_description = 'Activate selected contracts'

@admin.register(Parking)
class ParkingAdmin(admin.ModelAdmin):
    list_display = ('code', 'building', 'floor', 'status', 'unit', 'created_at', 'updated_at')
    list_filter = ('status', 'building', 'floor')
    search_fields = ('code', 'building__name', 'unit__unit_number')
    list_editable = ('status',)
    
    fieldsets = (
        ('Basic Information', {'fields': ('building', 'code', 'floor')}),
        ('Assignment', {'fields': ('unit', 'status')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('building', 'unit')

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('code', 'building', 'floor', 'area', 'status', 'unit', 'created_at', 'updated_at')
    list_filter = ('status', 'building', 'floor')
    search_fields = ('code', 'building__name', 'unit__unit_number')
    list_editable = ('status',)
    
    fieldsets = (
        ('Basic Information', {'fields': ('building', 'code', 'floor', 'area')}),
        ('Assignment', {'fields': ('unit', 'status')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('building', 'unit')