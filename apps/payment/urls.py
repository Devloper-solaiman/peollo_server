from django.urls import path
from apps.payment.views import (
                                CreatePaymentViews, 
                                WebhookView, 
                                BkashSandboxPaymentView,
                                BkashExecutePaymentView,
                                BkashQueryPaymentStatusView,
                                PaymentHistoryView,
                                DestroyPaymentHistoryView,
                                bkashCallBack
                                )


urlpatterns = [
    path('payment-history/', PaymentHistoryView.as_view(), name="payment-history"),
    path('delete/<int:pk>/', DestroyPaymentHistoryView.as_view(), name='delete-payment-history'),
    path('create-payment-intent/', CreatePaymentViews.as_view(), name="payment-intent"),
    path('stripe/webhook/', WebhookView.as_view(), name='stripe-webhook'),
    path('bkash/sandbox-payment/', BkashSandboxPaymentView.as_view(), name='bkash-sandbox-payment'),
    path('bkash/execute-payment/', BkashExecutePaymentView.as_view(), name='bkash-execute-payment'),
    path('bkash/query-payment-status/', BkashQueryPaymentStatusView.as_view(), name='bkash-query-payment-status'),
    path('bkash/callback/', bkashCallBack, name='callbackUrl')
]
# speedy-vouch-holy-remedy