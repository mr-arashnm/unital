from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Contract, Unit, UnitTransferHistory

@receiver(pre_save, sender=Unit)
def track_unit_changes(sender, instance, **kwargs):
    """
    ردیابی تغییرات واحد قبل از ذخیره شدن
    """
    if instance.pk:  # فقط برای واحدهای موجود
        try:
            old_instance = Unit.objects.get(pk=instance.pk)
            instance._old_owner = old_instance.owner
            instance._old_resident = old_instance.current_resident
        except Unit.DoesNotExist:
            instance._old_owner = None
            instance._old_resident = None

@receiver(post_save, sender=Unit)
def create_transfer_history(sender, instance, created, **kwargs):
    """
    ایجاد خودکار تاریخچه پس از تغییر واحد
    """
    if created:
        # برای واحدهای جدید
        if instance.owner:
            UnitTransferHistory.objects.create(
                unit=instance,
                transfer_type='ownership',
                previous_owner=None,
                new_owner=instance.owner,
                previous_resident=None,
                new_resident=instance.current_resident,
                transfer_date=timezone.now().date(),
                description='ثبت اولیه واحد در سیستم',
                recorded_by=instance.owner
            )
    else:
        # برای واحدهای موجود - بررسی تغییرات
        old_owner = getattr(instance, '_old_owner', None)
        old_resident = getattr(instance, '_old_resident', None)
        
        transfer_type = None
        description_parts = []
        
        # بررسی تغییر مالکیت
        if old_owner != instance.owner:
            transfer_type = 'ownership'
            description_parts.append(f'تغییر مالکیت از {old_owner} به {instance.owner}')
        
        # بررسی تغییر سکونت
        if old_resident != instance.current_resident:
            if transfer_type:
                transfer_type = 'both'
            else:
                transfer_type = 'residency'
            description_parts.append(f'تغییر سکونت از {old_resident} به {instance.current_resident}')
        
        # اگر تغییری رخ داده باشد
        if transfer_type:
            UnitTransferHistory.objects.create(
                unit=instance,
                transfer_type=transfer_type,
                previous_owner=old_owner,
                new_owner=instance.owner,
                previous_resident=old_resident,
                new_resident=instance.current_resident,
                transfer_date=timezone.now().date(),
                description=' | '.join(description_parts),
                recorded_by=instance.owner or instance.current_resident
            )
            
@receiver(post_save, sender=Contract)
def handle_contract_activation(sender, instance, created, **kwargs):
    """
    مدیریت فعال‌سازی قرارداد و ایجاد خودکار تاریخچه
    """
    if instance.status == 'active' and not created:
        # قرارداد فعال شده - تغییرات را اعمال کن
        if instance.contract_type == 'purchase':
            # ایجاد تاریخچه برای تغییر مالکیت
            UnitTransferHistory.objects.create(
                unit=instance.unit,
                transfer_type='ownership',
                previous_owner=instance.unit.owner,
                new_owner=instance.second_party,
                previous_resident=instance.unit.current_resident,
                new_resident=instance.unit.current_resident,
                transfer_date=instance.signed_date or timezone.now().date(),
                contract_number=instance.contract_number,
                contract_date=instance.signed_date,
                description=f'فروش واحد بر اساس قرارداد {instance.contract_number}',
                recorded_by=instance.created_by
            )
            
        elif instance.contract_type == 'rental':
            # ایجاد تاریخچه برای تغییر سکونت
            UnitTransferHistory.objects.create(
                unit=instance.unit,
                transfer_type='residency',
                previous_owner=instance.unit.owner,
                new_owner=instance.unit.owner,
                previous_resident=instance.unit.current_resident,
                new_resident=instance.second_party,
                transfer_date=instance.signed_date or timezone.now().date(),
                contract_number=instance.contract_number,
                contract_date=instance.signed_date,
                description=f'اجاره واحد بر اساس قرارداد {instance.contract_number}',
                recorded_by=instance.created_by
            )