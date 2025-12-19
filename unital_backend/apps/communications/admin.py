from django.contrib import admin
from .models import Notification, Meeting, MeetingAttendance, MeetingMinute, Announcement, SupportTicket, TicketResponse

class MeetingAttendanceInline(admin.TabularInline):
    model = MeetingAttendance
    extra = 0
    fields = ('user', 'status', 'responded_at', 'actual_attendance')
    readonly_fields = ('responded_at',)
    show_change_link = True

class TicketResponseInline(admin.TabularInline):
    model = TicketResponse
    extra = 0
    fields = ('responded_by', 'message', 'is_internal', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'complex', 'notification_type', 'target_type', 'is_sent', 'created_by', 'created_at')
    list_filter = ('notification_type', 'target_type', 'is_sent', 'created_at')
    search_fields = ('title', 'complex__name', 'message')
    readonly_fields = ('sent_at', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Notification information', {'fields': ('title', 'message', 'notification_type', 'target_type')}),
        ('Recipients', {'fields': ('specific_users', 'complex')}),
        ('Scheduling', {'fields': ('is_sent', 'scheduled_at', 'sent_at')}),
        ('Management', {'fields': ('created_by',)}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    filter_horizontal = ('specific_users',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('complex', 'created_by')

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('title', 'meeting_type', 'status', 'scheduled_date', 'location', 'duration', 'complex', 'created_by')
    list_filter = ('meeting_type', 'status', 'scheduled_date', 'complex')
    search_fields = ('title', 'agenda', 'location', 'created_by__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Meeting information', {'fields': ('title', 'meeting_type', 'description', 'agenda')}),
        ('Time & location', {'fields': ('scheduled_date', 'location', 'duration')}),
        ('Management', {'fields': ('complex', 'created_by')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    inlines = [MeetingAttendanceInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('complex', 'created_by')

@admin.register(MeetingMinute)
class MeetingMinuteAdmin(admin.ModelAdmin):
    list_display = ('meeting', 'created_by', 'created_at')
    search_fields = ('meeting__title', 'content')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Minute information', {'fields': ('meeting',)}),
        ('Content', {'fields': ('content', 'decisions', 'action_items')}),
        ('Signatories', {'fields': ('signed_by',)}),
        ('Management', {'fields': ('created_by',)}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    filter_horizontal = ('signed_by',)

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'complex', 'priority', 'is_published', 'publish_date', 'expiry_date', 'created_by')
    list_filter = ('priority', 'is_published', 'publish_date', 'complex')
    search_fields = ('title', 'content', 'complex__name')
    list_editable = ('is_published', 'priority')
    
    fieldsets = (
        ('Announcement information', {'fields': ('title', 'content', 'priority')}),
        ('Target', {'fields': ('complex', 'target_units')}),
        ('Publication', {'fields': ('is_published', 'publish_date', 'expiry_date')}),
        ('Management', {'fields': ('created_by',)}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    filter_horizontal = ('target_units',)

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'submitted_by', 'unit', 'ticket_type', 'status', 'priority', 'submitted_at', 'assigned_to')
    list_filter = ('status', 'ticket_type', 'priority', 'submitted_at')
    search_fields = ('title', 'submitted_by__email', 'unit__unit_number', 'description')
    readonly_fields = ('submitted_at', 'assigned_at', 'resolved_at', 'closed_at')
    
    fieldsets = (
        ('Ticket information', {'fields': ('title', 'description', 'ticket_type', 'priority')}),
        ('Status', {'fields': ('status', 'assigned_to')}),
        ('User & unit', {'fields': ('submitted_by', 'unit')}),
        ('Times', {'fields': ('submitted_at', 'assigned_at', 'resolved_at', 'closed_at')}),
    )
    
    inlines = [TicketResponseInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('submitted_by', 'unit', 'assigned_to')

admin.site.register([MeetingAttendance, TicketResponse])