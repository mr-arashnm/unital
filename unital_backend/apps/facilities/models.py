from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import User
from apps.complexes.models import Building, Unit
from decimal import Decimal

class Facility(models.Model):
    FACILITY_TYPES = (
        ('pool', 'Pool'),
        ('gym', 'Gym'),
        ('roof_garden', 'Roof garden'),
        ('meeting_room', 'Meeting room'),
        ('party_hall', 'Party hall'),
        ('guest_parking', 'Guest parking'),
        ('playground', 'Playground'),
        ('sports_court', 'Sports court'),
        ('library', 'Library'),
        ('business_center', 'Business center'),
        ('other', 'Other'),
    )
    
    complex = models.ForeignKey(
        Building, 
        on_delete=models.CASCADE, 
        related_name='facilities',
        verbose_name='Complex'
    )
    name = models.CharField(max_length=100, verbose_name='Name')
    facility_type = models.CharField(max_length=20, choices=FACILITY_TYPES, verbose_name='Facility type')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    
    # Capacity and restrictions
    capacity = models.PositiveIntegerField(verbose_name='Capacity')
    min_advance_booking = models.PositiveIntegerField(
        default=1,
        verbose_name='Minimum advance booking (hours)'
    )
    max_advance_booking = models.PositiveIntegerField(
        default=168,
        verbose_name='Maximum advance booking (hours)'
    )
    
    # Opening hours
    opening_time = models.TimeField(verbose_name='Opening time')
    closing_time = models.TimeField(verbose_name='Closing time')
    
    # Rules and cost
    rules = models.TextField(blank=True, null=True, verbose_name='Usage rules')
    hourly_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        default=0,
        verbose_name='Hourly rate'
    )
    is_free = models.BooleanField(default=True, verbose_name='Is free')
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='Is active')
    under_maintenance = models.BooleanField(default=False, verbose_name='Under maintenance')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Facility'
        verbose_name_plural = 'Facilities'
        ordering = ['complex', 'facility_type']
    
    def __str__(self):
        return f"{self.name} - {self.complex.name}"

    def is_open_during(self, start_dt, end_dt) -> bool:
        """Return True if the facility is open during the given datetime range.

        This checks the facility's opening_time/closing_time against the provided
        datetimes. It assumes opening and closing times are in the same day and
        does a simple time-of-day check. If closing_time is earlier than
        opening_time (overnight), it treats the facility as open across midnight.
        """
        if start_dt is None or end_dt is None:
            return False

        start_time = start_dt.time()
        end_time = end_dt.time()

        open_t = self.opening_time
        close_t = self.closing_time

        # if open and close are the same, assume open 24h
        if open_t == close_t:
            return True

        if open_t < close_t:
            # normal same-day window
            return (start_time >= open_t) and (end_time <= close_t)
        else:
            # overnight window (e.g., open at 20:00, close at 04:00)
            # open if start after open_t OR end before close_t
            return (start_time >= open_t) or (end_time <= close_t)

class FacilityBooking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending approval'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    )
    
    facility = models.ForeignKey(
        Facility, 
        on_delete=models.CASCADE, 
        related_name='bookings',
        verbose_name='Facility'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='facility_bookings',
        verbose_name='User'
    )
    
    # Scheduling
    start_time = models.DateTimeField(verbose_name='Start time')
    end_time = models.DateTimeField(verbose_name='End time')
    duration_hours = models.PositiveIntegerField(verbose_name='Duration (hours)')
    
    # Booking details
    purpose = models.CharField(max_length=200, verbose_name='Purpose')
    participants_count = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Participants count'
    )
    special_requirements = models.TextField(blank=True, null=True, verbose_name='Special requirements')
    
    # Status and approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Status')
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_bookings',
        limit_choices_to={'user_type__in': ['manager', 'staff']},
        verbose_name='Approved by'
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='Approved at')
    
    # Cost
    total_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        default=0,
        verbose_name='Total cost'
    )
    is_paid = models.BooleanField(default=False, verbose_name='Is paid')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Facility booking'
        verbose_name_plural = 'Facility bookings'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.facility.name} - {self.user} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate duration
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            # ensure an integer number of hours (use floor)
            self.duration_hours = int(duration.total_seconds() // 3600)
        
        # Calculate cost
        if not self.facility.is_free:
            # use Decimal for monetary calculation
            self.total_cost = Decimal(self.duration_hours) * Decimal(self.facility.hourly_rate)
        
        super().save(*args, **kwargs)

class FacilityMaintenance(models.Model):
    MAINTENANCE_TYPES = (
        ('routine', 'Routine'),
        ('repair', 'Repair'),
        ('cleaning', 'Cleaning'),
        ('inspection', 'Inspection'),
        ('upgrade', 'Upgrade'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    facility = models.ForeignKey(
        Facility, 
        on_delete=models.CASCADE, 
        related_name='maintenances',
        verbose_name='Facility'
    )
    title = models.CharField(max_length=200, verbose_name='title')
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES, verbose_name='Maintenance type')
    description = models.TextField(verbose_name='Description')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='Priority')
    
    # Scheduling
    scheduled_start = models.DateTimeField(verbose_name='Scheduled start')
    scheduled_end = models.DateTimeField(verbose_name='Scheduled end')
    actual_start = models.DateTimeField(null=True, blank=True, verbose_name='Actual start')
    actual_end = models.DateTimeField(null=True, blank=True, verbose_name='Actual end')
    
    # Status
    status = models.CharField(
        max_length=20, 
        choices=FacilityBooking.STATUS_CHOICES, 
        default='pending',
        verbose_name='Status'
    )
    
    # Assigned person
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'user_type': 'staff'},
        related_name='assigned_facility_maintenances',
        verbose_name='Assigned to'
    )
    
    # Affects bookings
    affect_bookings = models.BooleanField(default=True, verbose_name='Affects bookings')
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_facility_maintenances',
        verbose_name='Created by'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Facility maintenance'
        verbose_name_plural = 'Facility maintenances'
        ordering = ['-scheduled_start']
    
    def __str__(self):
        return f"{self.title} - {self.facility.name}"

class FacilityUsageRule(models.Model):
    facility = models.ForeignKey(
        Facility, 
        on_delete=models.CASCADE, 
        related_name='usage_rules',
        verbose_name='Facility'
    )
    rule = models.TextField(verbose_name='Rule')
    is_mandatory = models.BooleanField(default=True, verbose_name='Is mandatory')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Usage rule'
        verbose_name_plural = 'Usage rules'
    
    def __str__(self):
        return f"{self.facility.name} - {self.rule[:50]}..."

class FacilityImage(models.Model):
    facility = models.ForeignKey(
        Facility, 
        on_delete=models.CASCADE, 
        related_name='images',
        verbose_name='Facility'
    )
    image = models.ImageField(upload_to='facility_images/', verbose_name='image')
    caption = models.CharField(max_length=200, blank=True, null=True, verbose_name='title')
    is_primary = models.BooleanField(default=False, verbose_name='Is primary')
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Facility image'
        verbose_name_plural = 'Facility images'
    
    def __str__(self):
        return f"{self.facility.name} - {self.caption or 'Image'}"