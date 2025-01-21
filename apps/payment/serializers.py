from rest_framework import serializers
from apps.payment.models import Payment


class PaymentSerializers(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ['id', 'user', 'amount', 'plan',
                  'currency', 'stripe_payment_intent_id',
                  'bkash_transaction_id', "username",
                  'status', 'created_at', 'updated_at'
                  ]
        read_only_fields = ['id', 'status', 'plan', 'created_at', 'updated_at']
    
    def get_username(self, obj):
        return obj.user.first_name
        