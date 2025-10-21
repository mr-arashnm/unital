from django.utils import timezone
from django.db import models, transaction
from apps.accounts.models import User


class Building(models.Model):
    TYPES = (
        ('residential', 'residential'),
        ('commercial', 'commercial'),
        ('office', 'office'),
        ('mixed', 'mixed'),
    )
    
    name = models.CharField(max_length=200, verbose_name='name')
    code = models.CharField(max_length=50, unique=True, verbose_name='code')
    type = models.CharField(max_length=20, choices=TYPES, verbose_name='type')
    address = models.TextField(verbose_name='address')
    total_floors = models.IntegerField(verbose_name='total floors')
    total_units = models.IntegerField(verbose_name='total units')
    total_parkings = models.IntegerField(verbose_name='total parking')
    total_warehouses = models.IntegerField(verbose_name='total warehouses')
    description = models.TextField(blank=True, null=True, verbose_name='description')
    
    # management
    board_members = models.ManyToManyField(
        User, 
        related_name='managed_complexes',
        limit_choices_to={'user_type__in': ['manager', 'board_member']},
        verbose_name='board members'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_complexes',
        verbose_name='create by'
    )
    
    # زمان‌ها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='create time')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='last update')
    
    class Meta:
        verbose_name = 'building'
        verbose_name_plural = 'buildings'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Unit(models.Model):
    UNIT_STATUS = (
        ('occupied', 'Occupied'),
        ('vacant', 'Vacant'),
        ('under_construction', 'Under Construction'),
    )
    
    building = models.ForeignKey(
        Building, 
        on_delete=models.CASCADE, 
        related_name='units',
    )
    floor = models.IntegerField(verbose_name='Floor')
    unit_number = models.CharField(max_length=20, verbose_name='Unit Number')
    area = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Area (m²)')

    # owner and resident
    owner = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='owned_units',
        limit_choices_to={'user_type__in': ['owner', 'resident']},
        verbose_name='Owner'
    )
    resident = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='residing_units', 
        limit_choices_to={'user_type__in': ['resident', 'owner']},
        verbose_name='Resident'
    )
    
    status = models.CharField(
        max_length=20, 
        choices=UNIT_STATUS, 
        default='vacant',
        verbose_name='Status'
    )
    
    # additional info
    rooms = models.IntegerField(default=1, verbose_name='Number of Rooms')

    # time create and update
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creation Time')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Last Updated')

    class Meta:
        verbose_name = 'Unit'
        verbose_name_plural = 'Units'
        unique_together = ['building', 'unit_number']
        ordering = ['building', 'floor', 'unit_number']
    
    def __str__(self):
        return f"Unit {self.unit_number} - {self.building.name}"
    
    # parkings
    @property
    def assigned_parkings(self):
        """get this unit parking"""
        return self.parkings.all()
    
    def get_available_parkings(self):
        """get available parkings in the building"""
        return Parking.objects.filter(
            building=self.building,
            status='available'
        )
    
    def assign_parking(self, parking_code):
        """allocation parking to unit"""
        try:
            parking = Parking.objects.get(
                code=parking_code,
                building=self.building,
                status='available'
            )
            success, message = parking.assign_to_unit(self)
            return success, message
        except Parking.DoesNotExist:
            return False, "Parking not found or not available"
    
    def release_parking(self, parking_code):
        """deallocate parking from unit"""
        try:
            parking = self.parkings.get(code=parking_code)
            return parking.release_from_unit()
        except Parking.DoesNotExist:
            return False, "Parking not assigned to this unit"
    
    # warehouses
    @property
    def assigned_warehouses(self):
        """get this unit warehouses"""
        return self.warehouses.all()
    
    def get_available_warehouses(self):
        """get available warehouses in the building"""
        return Warehouse.objects.filter(
            building=self.building,
            status='available'
        )
    
    def assign_warehouse(self, warehouse_code):
        """allocate warehouse to unit"""
        try:
            warehouse = Warehouse.objects.get(
                code=warehouse_code,
                building=self.building,
                status='available'
            )
            return warehouse.assign_to_unit(self)
        except Warehouse.DoesNotExist:
            return False, "Warehouse not found or not available"
    
    def release_warehouse(self, warehouse_code):
        """deallocate warehouse from unit"""
        try:
            warehouse = self.warehouses.get(code=warehouse_code)
            return warehouse.release_from_unit()
        except Warehouse.DoesNotExist:
            return False, "Warehouse not assigned to this unit"

    # properties
    @property
    def full_address(self):
        return f"{self.building.address} - Building {self.building.name} - Unit {self.unit_number}"

    @property
    def has_parking(self):
        """Does this unit have parking?"""
        return self.parkings.exists()
    
    @property
    def has_warehouse(self):
        """Does this unit have a warehouse?"""
        return self.warehouses.exists()
    
    @property
    def total_parking_count(self):
        """Total number of parkings allocated to this unit"""
        return self.parkings.count()
    
    @property
    def total_warehouse_count(self):
        """Total number of warehouses allocated to this unit"""
        return self.warehouses.count()
    
    # manage ownership and resident 
    def change_ownership(self, new_owner, transfer_date, contract_number=None, recorded_by=None, description=None):
        """change unit ownership and log history"""
        with transaction.atomic():
            previous_owner = self.owner
            # create history record
            UnitTransferHistory.objects.create(
                unit=self,
                transfer_type='ownership',
                previous_owner=previous_owner,
                new_owner=new_owner,
                previous_resident=self.resident,
                new_resident=self.resident,
                transfer_date=transfer_date,
                contract_number=contract_number,
                contract_date=transfer_date,
                description=description,
                recorded_by=recorded_by
            )
            
            # update current owner
            self.owner = new_owner
            self.save()
            
        return True, "Ownership changed successfully"
    
    def change_residency(self, new_resident, transfer_date, description=None, recorded_by=None):
        """change unit residency and log history"""
        with transaction.atomic():
            previous_resident = self.resident
            # create history record
            UnitTransferHistory.objects.create(
                unit=self,
                transfer_type='residency',
                previous_owner=self.owner,
                new_owner=self.owner,
                previous_resident=previous_resident,
                new_resident=new_resident,
                transfer_date=transfer_date,
                description=description,
                recorded_by=recorded_by
            )
            # update current resident
            self.resident = new_resident
            self.save()
            
        return True
    
    def get_transfer_history(self):
        """get full transfer history of the unit"""
        return self.transfer_history.all()
    
    def get_ownership_history(self):
        """get ownership history"""
        return self.transfer_history.filter(
            transfer_type__in=['ownership', 'both']
        )
    
    def get_residency_history(self):
        """get residency history"""
        return self.transfer_history.filter(
            transfer_type__in=['residency', 'both']
        ) 
    
class Parking(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('occupied', 'Occupied'),
    )
    
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name='parkings',
        verbose_name='Building'
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parkings',
        verbose_name='Assigned Unit'
    )
    floor = models.IntegerField(verbose_name='Floor')
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Parking Code'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available',
        verbose_name='Status'
    )
    
    # اضافه کردن فیلدهای زمانی
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Last Updated')
    
    class Meta:
        verbose_name = 'parking'
        verbose_name_plural = 'parkings'
        ordering = ['building', 'floor', 'code']
    
    def __str__(self):
        return f"Parking {self.code} - {self.building.name}"
    
    def assign_to_unit(self, unit):
        """تخصیص پارکینگ به واحد"""
        if self.status == 'occupied':
            return False, "Parking is already occupied"

        # بررسی اینکه واحد در همان ساختمان باشد
        if unit.building != self.building:
            return False, "Unit is not in the same building"

        self.unit = unit
        self.status = 'occupied'
        self.save()
        return True, "Parking assigned successfully"
    
    def release_from_unit(self):
        """آزادسازی پارکینگ از واحد"""
        self.unit = None
        self.status = 'available'
        self.save()
        return True, "Parking released successfully"
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('occupied', 'Occupied'),
    )
    
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name='parkings',
        verbose_name='Building'
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,  # مهم: با حذف واحد، پارکینگ آزاد شود
        null=True,
        blank=True,
        related_name='parkings',
        verbose_name='Assigned Unit'
    )
    floor = models.IntegerField(verbose_name='Floor')
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Parking Code'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available',
        verbose_name='Status'
    )
    
    class Meta:
        verbose_name = 'parking'
        verbose_name_plural = 'parkings'
        ordering = ['building', 'floor', 'code']
    
    def __str__(self):
        return f"Parking {self.code} - {self.building.name}"
    
    def assign_to_unit(self, unit):
        """Assign parking to unit"""
        if self.status == 'occupied':
            return False, "Parking is already occupied"

        # verify that the unit is in the same building
        if unit.building != self.building:
            return False, "Unit is not in the same building"

        self.unit = unit
        self.status = 'occupied'
        self.save()
        return True, "Parking assigned successfully"
    
    def release_from_unit(self):
        """Release parking from unit"""
        self.unit = None
        self.status = 'available'
        self.save()
        return True, "Parking released successfully"
    
class Warehouse(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('occupied', 'Occupied'),
    )
    
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name='warehouses',
        verbose_name='Building'
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='warehouses',
        verbose_name='Assigned Unit'
    )
    floor = models.IntegerField(verbose_name='Floor')
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Warehouse Code'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available',
        verbose_name='Status'
    )
    area = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Area (m²)'
    )
    
    # اضافه کردن فیلدهای زمانی
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Last Updated')
    
    class Meta:
        verbose_name = 'warehouse'
        verbose_name_plural = 'warehouses'
        ordering = ['building', 'floor', 'code']
    
    def __str__(self):
        return f"Warehouse {self.code} - {self.building.name}"
    
    def assign_to_unit(self, unit):
        """تخصیص انباری به واحد"""
        if self.status == 'occupied':
            return False, "Warehouse is already occupied"
        
        # بررسی اینکه واحد در همان ساختمان باشد
        if unit.building != self.building:
            return False, "Unit is not in the same building"
        
        self.unit = unit
        self.status = 'occupied'
        self.save()
        return True, "Warehouse assigned successfully"
    
    def release_from_unit(self):
        """آزادسازی انباری از واحد"""
        self.unit = None
        self.status = 'available'
        self.save()
        return True, "Warehouse released successfully"
    
    def is_available(self):
        """بررسی در دسترس بودن انباری"""
        return self.status == 'available'
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('occupied', 'Occupied'),
    )
    
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name='warehouses',
        verbose_name='Building'
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,  # مهم: با حذف واحد، انباری آزاد شود
        null=True,
        blank=True,
        related_name='warehouses',
        verbose_name='Assigned Unit'
    )
    floor = models.IntegerField(verbose_name='Floor')
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Warehouse Code'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available',
        verbose_name='Status'
    )
    area = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Area (m²)'
    )
    
    class Meta:
        verbose_name = 'warehouse'
        verbose_name_plural = 'warehouses'
        ordering = ['building', 'floor', 'code']
    
    def __str__(self):
        return f"Warehouse {self.code} - {self.building.name}"
    
    def assign_to_unit(self, unit):
        """Assign warehouse to unit"""
        if self.status == 'occupied':
            return False, "Warehouse is already occupied"
        
        # verify that the unit is in the same building
        if unit.building != self.building:
            return False, "Unit is not in the same building"
        
        self.unit = unit
        self.status = 'occupied'
        self.save()
        return True, "Warehouse assigned successfully"
    
    def release_from_unit(self):
        """Release warehouse from unit"""
        self.unit = None
        self.status = 'available'
        self.save()
        return True, "Warehouse released successfully"
    
    def is_available(self):
        """Check if warehouse is available"""
        return self.status == 'available'
    
class UnitTransferHistory(models.Model):
    TRANSFER_TYPES = (
        ('ownership', 'change of ownership'),
        ('residency', 'change of residency'),
        ('both', 'change of ownership and residency'),
    )
    
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        related_name='transfer_history',
        verbose_name='unit'
    )
    
    transfer_type = models.CharField(
        max_length=20, 
        choices=TRANSFER_TYPES, 
        verbose_name='transfer type'
    )
    
    # last owner/resident
    previous_owner = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='previous_ownerships',
        verbose_name='last owner'
    )
    previous_resident = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='previous_residencies', 
        verbose_name='last resident'
    )
    
    # new owner/resident
    new_owner = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='new_ownerships',
        verbose_name='new owner'
    )
    new_resident = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='new_residencies',
        verbose_name='new resident'
    )
    
    # transfer info
    transfer_date = models.DateField(verbose_name='transfer date')
    contract_number = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='contract number'
    )
    contract_date = models.DateField(
        blank=True, 
        null=True,
        verbose_name='contract time'
    )
    #contract_end_date
    description = models.TextField(
        blank=True, 
        null=True,
        verbose_name='description'
    )
    # record by
    recorded_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        verbose_name='recorded by'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'unit transfer history'
        verbose_name_plural = 'unit transfer histories'
        ordering = ['-transfer_date', '-created_at']
    
    def __str__(self):
        return f"{self.unit} - {self.get_transfer_type_display()} - {self.transfer_date}"  
    
class Contract(models.Model):
    CONTRACT_TYPES = (
        ('purchase', 'Purchase and sale agreement'),
        ('rental', 'Rental agreement'),
        ('transfer', 'Transfer agreement'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    
    # Parties to the contract
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        related_name='contracts',
        verbose_name='unit'
    )
    contract_type = models.CharField(
        max_length=20, 
        choices=CONTRACT_TYPES, 
        verbose_name='contract type'
    )
    
    # Parties to the contract
    first_party = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='contracts_as_first_party',
        verbose_name='First Party'
    )
    second_party = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='contracts_as_second_party', 
        verbose_name='Second Party'
    )
    # Parties info
    contract_number = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name='number of contract'
    )
    title = models.CharField(max_length=200, verbose_name='title of contract')
    description = models.TextField(blank=True, null=True, verbose_name='description of contract')

    # Duration of contract
    start_date = models.DateField(verbose_name='start date')
    end_date = models.DateField(blank=True, null=True, verbose_name='end date')
    duration_months = models.PositiveIntegerField(verbose_name='duration of contract (months)')

    # Financial
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=0, 
        verbose_name='amount of contract'
    )
    deposit_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=0, 
        default=0,
        verbose_name='deposit amount'
    )
    # status
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        verbose_name='status'
    )
    
    # files
    contract_file = models.FileField(
        upload_to='contracts/',
        blank=True, 
        null=True,
        verbose_name='contract file'
    )

    # Signatures
    first_party_signed = models.BooleanField(default=False, verbose_name='First Party Signature')
    second_party_signed = models.BooleanField(default=False, verbose_name='Second Party Signature')
    signed_date = models.DateField(blank=True, null=True, verbose_name='signed date')
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        related_name='created_contracts',
        verbose_name='created by'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'contract'
        verbose_name_plural = 'contracts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.contract_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        # create unique contract number if not set
        if not self.contract_number:
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
        """Activate the contract and apply necessary changes"""
        if self.status != 'draft':
            return False, "Contract is not in draft status"
        
        # Apply changes based on contract type
        if self.contract_type == 'purchase':
            # Change ownership
            self.unit.owner = self.second_party
            self.unit.save()
            
        elif self.contract_type == 'rental':
            # Change resident
            self.unit.resident = self.second_party
            self.unit.save()
        
        self.status = 'active'
        self.signed_date = timezone.now().date()
        self.save()
        
        return True, "Contract activated successfully"
