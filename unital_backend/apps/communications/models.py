from django.db import models
from apps.accounts.models import User
from apps.complexes.models import Building, Unit
from django.db.models import JSONField


class Team(models.Model):
    """Represents an internal team/department (e.g. security, gardening, maintenance)."""
    name = models.CharField(max_length=100, unique=True, verbose_name='Name')
    members = models.ManyToManyField(User, blank=True, related_name='teams', verbose_name='Members')

    class Meta:
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'

    def __str__(self):
        return self.name

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('charge', 'Charge'),
        ('meeting', 'Meeting'),
        ('maintenance', 'Maintenance'),
        ('security', 'Security'),
        ('general', 'General'),
        ('urgent', 'Urgent'),
    )
    
    TARGET_TYPES = (
        ('all', 'All residents'),
        ('owners', 'Owners'),
        ('residents', 'Residents'),
        ('board', 'Board'),
        ('specific', 'Specific users'),
    )
    
    title = models.CharField(max_length=200, verbose_name='Title')
    message = models.TextField(verbose_name='Message')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name='Notification type')
    target_type = models.CharField(max_length=20, choices=TARGET_TYPES, verbose_name='Recipients')
    
    # مخاطبان خاص
    specific_users = models.ManyToManyField(
        User, 
        blank=True,
        verbose_name='Specific users'
    )

    # allow targeting by role(s) (e.g. ['owner','resident','manager'])
    target_roles = JSONField(default=list, blank=True)

    # target specific teams/departments (see Team model below)
    # teams are optional and allow a message to be visible to multiple groups
    target_teams = models.ManyToManyField('Team', blank=True, verbose_name='Target teams')
    
    # Related complex
    complex = models.ForeignKey(
        Building, 
        on_delete=models.CASCADE, 
        verbose_name='Complex'
    )
    
    # Send status
    is_sent = models.BooleanField(default=False, verbose_name='Is sent')
    scheduled_at = models.DateTimeField(null=True, blank=True, verbose_name='Scheduled at')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Sent at')
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_notifications',
        verbose_name='Created by'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.complex.name}"

class Meeting(models.Model):
    MEETING_TYPES = (
        ('board', 'Board'),
        ('general', 'General'),
        ('committee', 'Committee'),
        ('emergency', 'Emergency'),
    )
    
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    title = models.CharField(max_length=200, verbose_name='Title')
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPES, verbose_name='Meeting type')
    description = models.TextField(verbose_name='Description')
    agenda = models.TextField(verbose_name='Agenda')
    
    # Time and location
    scheduled_date = models.DateTimeField(verbose_name='Scheduled date')
    location = models.CharField(max_length=200, verbose_name='Location')
    duration = models.PositiveIntegerField(default=60, verbose_name='Duration (minutes)')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name='Status')
    
    # Attendees
    attendees = models.ManyToManyField(
        User,
        through='MeetingAttendance',
        related_name='meetings_attended',
        verbose_name='Attendees'
    )
    
    # Related complex
    complex = models.ForeignKey(
        Building, 
        on_delete=models.CASCADE, 
        verbose_name='Complex'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_meetings',
        verbose_name='Created by'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # allow meeting to target specific roles and/or teams
    target_roles = JSONField(default=list, blank=True)
    target_teams = models.ManyToManyField('Team', blank=True, verbose_name='Target teams')
    
    class Meta:
        verbose_name = 'Meeting'
        verbose_name_plural = 'Meetings'
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.title} - {self.scheduled_date.strftime('%Y-%m-%d')}"

class MeetingAttendance(models.Model):
    ATTENDANCE_STATUS = (
        ('invited', 'Invited'),
        ('confirmed', 'Confirmed'),
        ('declined', 'Declined'),
        ('attended', 'Attended'),
        ('absent', 'Absent'),
    )
    
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, verbose_name='Meeting')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='User')
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS, default='invited', verbose_name='Attendance status')
    
    # Times
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name='Responded at')
    actual_attendance = models.BooleanField(null=True, blank=True, verbose_name='Physical attendance')
    
    class Meta:
        verbose_name = 'Meeting attendance'
        verbose_name_plural = 'Meeting attendances'
        unique_together = ['meeting', 'user']
    
    def __str__(self):
        return f"{self.user} - {self.meeting.title}"

class MeetingMinute(models.Model):
    meeting = models.OneToOneField(
        Meeting, 
        on_delete=models.CASCADE, 
        related_name='minutes',
        verbose_name='Meeting'
    )
    content = models.TextField(verbose_name='Content')
    decisions = models.TextField(verbose_name='Decisions')
    action_items = models.TextField(verbose_name='Action items')
    
    # Signatories
    signed_by = models.ManyToManyField(
        User, 
        related_name='signed_minutes',
        verbose_name='Signatories'
    )
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        verbose_name='Recorded by'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Meeting minute'
        verbose_name_plural = 'Meeting minutes'
    
    def __str__(self):
        return f"Meeting minute {self.meeting.title}"

class Announcement(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    title = models.CharField(max_length=200, verbose_name='Title')
    content = models.TextField(verbose_name='Content')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal', verbose_name='Priority')
    
    # Target
    complex = models.ForeignKey(
        Building, 
        on_delete=models.CASCADE, 
        verbose_name='Complex'
    )
    target_units = models.ManyToManyField(
        Unit, 
        blank=True,
        verbose_name='Target units'
    )
    # allow announcement to target roles and/or teams
    target_roles = JSONField(default=list, blank=True)
    target_teams = models.ManyToManyField('Team', blank=True, verbose_name='Target teams')
    
    # Status
    is_published = models.BooleanField(default=False, verbose_name='Is published')
    publish_date = models.DateTimeField(null=True, blank=True, verbose_name='Publish date')
    expiry_date = models.DateTimeField(null=True, blank=True, verbose_name='Expiry date')
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        verbose_name='Created by'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'
        ordering = ['-publish_date', '-priority']
    
    def __str__(self):
        return self.title

class SupportTicket(models.Model):
    TICKET_TYPES = (
        ('technical', 'Technical'),
        ('financial', 'Financial'),
        ('complaint', 'Complaint'),
        ('suggestion', 'Suggestion'),
        ('general', 'General'),
    )
    
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    title = models.CharField(max_length=200, verbose_name='Ticket title')
    description = models.TextField(verbose_name='Description')
    ticket_type = models.CharField(max_length=20, choices=TICKET_TYPES, verbose_name='Ticket type')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', verbose_name='Status')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='Priority')
    
    # User and unit
    submitted_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='support_tickets',
        verbose_name='Submitted by'
    )
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        verbose_name='Unit'
    )
    
    # Assigned handler
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        limit_choices_to={'user_type__in': ['manager', 'staff']},
        verbose_name='Assigned to'
    )

    # optionally associate ticket with an internal team/department
    team = models.ForeignKey('Team', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Team/Department')
    
    # Times
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='Submitted at')
    assigned_at = models.DateTimeField(null=True, blank=True, verbose_name='Assigned at')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='Resolved at')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='Closed at')
    
    class Meta:
        verbose_name = 'Support ticket'
        verbose_name_plural = 'Support tickets'
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.title} - {self.submitted_by}"

class TicketResponse(models.Model):
    ticket = models.ForeignKey(
        SupportTicket, 
        on_delete=models.CASCADE, 
        related_name='responses',
        verbose_name='Ticket'
    )
    responded_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Responder'
    )
    message = models.TextField(verbose_name='Message')
    attachment = models.FileField(
        upload_to='ticket_attachments/', 
        null=True, 
        blank=True,
        verbose_name='Attachment'
    )
    is_internal = models.BooleanField(default=False, verbose_name='Internal response')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Ticket response'
        verbose_name_plural = 'Ticket responses'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Response to {self.ticket.title}"