from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import datetime
from .models import ChargeTemplate, Charge, Transaction, Invoice
from .serializers import (
    ChargeTemplateSerializer, ChargeSerializer, 
    TransactionSerializer, InvoiceSerializer
)
from apps.complexes.models import Complex, Unit

class ChargeTemplateViewSet(viewsets.ModelViewSet):
    queryset = ChargeTemplate.objects.filter(is_active=True)
    serializer_class = ChargeTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['manager', 'board_member']:
            return ChargeTemplate.objects.filter(complex__board_members=user)
        return ChargeTemplate.objects.none()

class ChargeViewSet(viewsets.ModelViewSet):
    queryset = Charge.objects.all()
    serializer_class = ChargeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['manager', 'board_member']:
            return Charge.objects.filter(unit__building__complex__board_members=user)
        elif user.user_type == 'owner':
            return Charge.objects.filter(unit__owner=user)
        elif user.user_type == 'resident':
            return Charge.objects.filter(unit__current_resident=user)
        return Charge.objects.none()
    
    @action(detail=False, methods=['post'])
    def generate_charges(self, request):
        """ایجاد خودکار شارژ برای تمام واحدهای یک مجتمع"""
        complex_id = request.data.get('complex_id')
        period = request.data.get('period')  # YYYY-MM
        
        try:
            complex = Complex.objects.get(id=complex_id, board_members=request.user)
            units = Unit.objects.filter(building__complex=complex)
            templates = ChargeTemplate.objects.filter(complex=complex, is_active=True)
            
            created_charges = []
            for unit in units:
                for template in templates:
                    charge, created = Charge.objects.get_or_create(
                        unit=unit,
                        template=template,
                        period=period,
                        defaults={
                            'amount': template.amount,
                            'due_date': f"{period}-25",  # 25ام هر ماه
                            'created_by': request.user
                        }
                    )
                    if created:
                        created_charges.append(charge)
            
            return Response({
                'message': f'{len(created_charges)} شارژ ایجاد شد',
                'created_charges': len(created_charges)
            })
            
        except Complex.DoesNotExist:
            return Response(
                {'error': 'مجتمع یافت نشد'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['manager', 'board_member']:
            return Transaction.objects.filter(charge__unit__building__complex__board_members=user)
        elif user.user_type in ['owner', 'resident']:
            return Transaction.objects.filter(charge__unit__owner=user)
        return Transaction.objects.none()
    
    @action(detail=True, methods=['post'])
    def confirm_payment(self, request, pk=None):
        """تأیید پرداخت تراکنش"""
        transaction = self.get_object()
        
        if transaction.status == 'completed':
            return Response(
                {'error': 'این تراکنش قبلاً تأیید شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transaction.status = 'completed'
        transaction.payment_date = timezone.now()
        transaction.save()
        
        # بروزرسانی شارژ مربوطه
        charge = transaction.charge
        charge.paid_amount += transaction.amount
        charge.remaining_amount = charge.amount - charge.paid_amount
        
        if charge.remaining_amount <= 0:
            charge.status = 'paid'
        elif charge.paid_amount > 0:
            charge.status = 'partially_paid'
            
        charge.save()
        
        return Response({'message': 'پرداخت با موفقیت تأیید شد'})

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['manager', 'board_member']:
            return Invoice.objects.filter(unit__building__complex__board_members=user)
        elif user.user_type in ['owner', 'resident']:
            return Invoice.objects.filter(unit__owner=user)
        return Invoice.objects.none()
    
    @action(detail=False, methods=['get'])
    def financial_report(self, request):
        """گزارش مالی برای مدیر"""
        complex_id = request.query_params.get('complex_id')
        period = request.query_params.get('period')
        
        if not complex_id:
            return Response(
                {'error': 'complex_id الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # آمار کلی
        total_charges = Charge.objects.filter(
            unit__building__complex_id=complex_id,
            period=period
        ).aggregate(
            total_amount=Sum('amount'),
            total_paid=Sum('paid_amount'),
            total_remaining=Sum('remaining_amount')
        )
        
        # تعداد واحدها بر اساس وضعیت پرداخت
        payment_stats = Charge.objects.filter(
            unit__building__complex_id=complex_id,
            period=period
        ).values('status').annotate(count=Count('id'))
        
        return Response({
            'period': period,
            'total_amount': total_charges['total_amount'] or 0,
            'total_paid': total_charges['total_paid'] or 0,
            'total_remaining': total_charges['total_remaining'] or 0,
            'payment_stats': list(payment_stats)
        })