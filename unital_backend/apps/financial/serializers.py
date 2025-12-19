from rest_framework import serializers
from .models import ChargeTemplate, Charge, Transaction, Invoice
from apps.complexes.serializers import UnitSerializer

class ChargeTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChargeTemplate
        fields = ['id', 'name', 'charge_type', 'amount', 'description', 'is_active']

class ChargeSerializer(serializers.ModelSerializer):
    unit_info = UnitSerializer(source='unit', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = Charge
        fields = [
            'id', 'unit', 'unit_info', 'template', 'template_name',
            'period', 'amount', 'due_date', 'status', 'paid_amount',
            'remaining_amount', 'description', 'created_at'
        ]

class TransactionSerializer(serializers.ModelSerializer):
    charge_info = ChargeSerializer(source='charge', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'charge', 'charge_info', 'amount', 'payment_method',
            'status', 'reference_id', 'payment_date', 'description',
            'created_at'
        ]

    def validate(self, data):
        charge = data.get('charge')
        amount = data.get('amount')
        if amount is None or amount <= 0:
            raise serializers.ValidationError({'amount': 'مبلغ تراکنش باید بزرگتر از صفر باشد'})

        # If charge provided, ensure we don't accept amounts greater than remaining_amount
        if charge is not None:
            remaining = charge.remaining_amount or charge.amount
            if amount > remaining:
                raise serializers.ValidationError({'amount': 'مبلغ تراکنش بیشتر از مبلغ باقیمانده شارژ است'})

        return data

class InvoiceSerializer(serializers.ModelSerializer):
    unit_info = UnitSerializer(source='unit', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'unit', 'unit_info', 'period', 'total_amount',
            'paid_amount', 'remaining_amount', 'is_paid', 'due_date',
            'created_at'
        ]