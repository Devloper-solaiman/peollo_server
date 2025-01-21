from django.db import models
from django.utils import timezone
from apps.account.models import User


class Payment(models.Model):
    class STATUS_TYPE(models.TextChoices):
        CREATED = 'CREATED', 'Created',
        SUCCEEDED = 'SUCCEEDED', 'Succeeded'
        PENDING = 'PENDING', 'Pending'
        FAILED = 'FAILED', 'Failed'
        CANCELED = 'CANCELED', 'Canceled'
    
    class PLAN_TYPE(models.TextChoices):
        BASIC = 'BASIC', 'Basic',
        PROFESSIONAL = 'PROFESSIONAL', 'Professional'
        CUSTOM = 'CUSTOM', 'Custom'

    class CURRENCY_TYPE(models.TextChoices):
        USD = 'USD', 'usd'
        BDT = 'BDT', 'bdt'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='BDT')
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    bkash_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    bkash_request_id = models.CharField(max_length=255, blank=True, null=True)
    plan = models.CharField(max_length=15, choices=PLAN_TYPE.choices, default=None)
    status = models.CharField(max_length=50, choices=STATUS_TYPE.choices, default=STATUS_TYPE.CREATED)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'Payment {self.id} - {self.status}'
    


