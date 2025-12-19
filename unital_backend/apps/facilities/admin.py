from django.contrib import admin
from .models import Facility, FacilityBooking, FacilityMaintenance, FacilityUsageRule, FacilityImage

class FacilityImageInline(admin.TabularInline):
    model = FacilityImage
    extra = 1
    fields = ('image', 'caption', 'is_primary')
    readonly_fields = ('uploaded_at',)

class FacilityBookingInline(admin.TabularInline):
    model = FacilityBooking
    extra = 0
    fields = ('user', 'start_time', 'end_time', 'status', 'purpose')
    readonly_fields = ('created_at',)
    show_change_link = True

class FacilityMaintenanceInline(admin.TabularInline):
    model = FacilityMaintenance
    extra = 0
    fields = ('title', 'maintenance_type', 'status', 'scheduled_start', 'assigned_to')
    readonly_fields = ('created_at',)
    show_change_link = True

class FacilityUsageRuleInline(admin.TabularInline):
    model = FacilityUsageRule
    extra = 1
    fields = ('rule', 'is_mandatory')

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'complex', 'facility_type', 'capacity', 'hourly_rate', 'is_free', 'is_active', 'under_maintenance')
    list_filter = ('facility_type', 'is_active', 'under_maintenance', 'is_free', 'complex')
    search_fields = ('name', 'complex__name', 'description')
    list_editable = ('is_active', 'under_maintenance', 'hourly_rate')
    
    fieldsets = (
        ('Facility information', {'fields': ('complex', 'name', 'facility_type', 'description')}),
        ('Capacity and scheduling', {'fields': ('capacity', 'min_advance_booking', 'max_advance_booking', 'opening_time', 'closing_time')}),
        ('Cost and rules', {'fields': ('hourly_rate', 'is_free', 'rules')}),
        ('Status', {'fields': ('is_active', 'under_maintenance')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    inlines = [FacilityImageInline, FacilityBookingInline, FacilityMaintenanceInline, FacilityUsageRuleInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('complex')

@admin.register(FacilityBooking)
class FacilityBookingAdmin(admin.ModelAdmin):
    list_display = ('facility', 'user', 'start_time', 'end_time', 'duration_hours', 'status', 'purpose', 'participants_count', 'total_cost')
    list_filter = ('status', 'facility__facility_type', 'start_time', 'facility__complex')
    search_fields = ('facility__name', 'user__email', 'purpose')
    readonly_fields = ('created_at', 'updated_at', 'approved_at', 'duration_hours')
    
    fieldsets = (
        ('Booking information', {'fields': ('facility', 'user', 'purpose', 'participants_count', 'special_requirements')}),
        ('Scheduling', {'fields': ('start_time', 'end_time', 'duration_hours')}),
        ('Status & approval', {'fields': ('status', 'approved_by', 'approved_at')}),
        ('Cost', {'fields': ('total_cost', 'is_paid')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('facility', 'user', 'approved_by')

@admin.register(FacilityMaintenance)
class FacilityMaintenanceAdmin(admin.ModelAdmin):
    list_display = ('facility', 'title', 'maintenance_type', 'priority', 'status', 'scheduled_start', 'assigned_to', 'affect_bookings')
    list_filter = ('status', 'maintenance_type', 'priority', 'scheduled_start', 'facility__complex')
    search_fields = ('title', 'facility__name', 'description')
    list_editable = ('status', 'priority')
    
    fieldsets = (
        ('Maintenance information', {'fields': ('facility', 'title', 'maintenance_type', 'description', 'priority')}),
        ('Scheduling', {'fields': ('scheduled_start', 'scheduled_end', 'actual_start', 'actual_end')}),
        ('Status & assignee', {'fields': ('status', 'assigned_to', 'affect_bookings')}),
        ('Management', {'fields': ('created_by',)}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('facility', 'assigned_to', 'created_by')

admin.site.register([FacilityUsageRule, FacilityImage])