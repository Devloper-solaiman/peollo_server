import stripe 
import requests
import uuid
from django.shortcuts import redirect
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from rest_framework import status, views, generics
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
import stripe.webhook
from apps.payment.models import Payment
from apps.payment.serializers import PaymentSerializers

stripe.api_key = settings.STRIPE_SECRET_KEY


def generate_bkash_sandbox_token():
    url = f"{settings.BKASH_SANDBOX_BASE_URL}/tokenized/checkout/token/grant"
    # print(url)
    headers = {
        'Content-Type': 'application/json',
        "Accept": "application/json",
        'username': settings.BKASH_SANDBOX_USERNAME,
        'password': settings.BKASH_SANDBOX_PASSWORD
    }

    payload = {
        'app_key': settings.BKASH_SANDBOX_APP_KEY,
        'app_secret': settings.BKASH_SANDBOX_APP_SECRET
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get('id_token')
        else:
            raise Exception("Failed to obtain bKash sandbox token")
    except Exception as e:
        print(f"Error in token generation: {str(e)}")
        raise


def create_sandbox_payment_request(amount, merchent_invoice_number):
    token = generate_bkash_sandbox_token()
    url = f"{settings.BKASH_SANDBOX_BASE_URL}/tokenized/checkout/create"
    headers = {
        'Content-Type': 'application/json',
        "Accept": "application/json",
        'Authorization': f'Bearer {token}',
        'X-App-Key': settings.BKASH_SANDBOX_APP_KEY,
    }

    payload = {
        'mode': '0011',
        'payerReference': merchent_invoice_number,
        'callbackURL': 'https://mdsolaimandeveloper.pythonanywhere.com/api/payment/bkash/callback/',
        'amount': str(amount),
        'currency': "BDT",
        'intent': "sale",
        'merchantInvoiceNumber': merchent_invoice_number
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()


def excute_sandbox_payment(payment_id):
    token = generate_bkash_sandbox_token()

    url = f"{settings.BKASH_SANDBOX_BASE_URL}/tokenized/checkout/execute"
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}',
        'X-App-Key': settings.BKASH_SANDBOX_APP_KEY,
    }
    
    payload = {
        "paymentID": payment_id
    }

    response = requests.post(url, headers=headers, json=payload)
    print(response.text)

    return response.json()


def query_sandbox_payment_status(payment_id):
    token = generate_bkash_sandbox_token()

    url = f"{settings.BKASH_SANDBOX_BASE_URL}/tokenized/checkout/payment/status"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}',
        'X-App-Key': settings.BKASH_SANDBOX_APP_KEY
    }
    
    payload = {
        "paymentID": payment_id
    }

    response = requests.post(url, headers=headers, json=payload)

    # print(response.text)
    return response.json()


def credit_user_based_on_plan(payment):
    user = payment.user
    # print(user)
    if payment.plan == Payment.PLAN_TYPE.BASIC:
        user.is_basic = True
        user.credit += 10
    elif payment.plan == Payment.PLAN_TYPE.PROFESSIONAL:
        user.is_professional = True
        user.credit += 490
    elif payment.plan == Payment.PLAN_TYPE.CUSTOM:
        user.is_custom = True
        price = float(payment.amount)
        # print(price)
        credit = 10*(price/105)
        user.credit += credit
    user.save()
    payment.status = Payment.STATUS_TYPE.SUCCEEDED
    payment.save()


class CreatePaymentViews(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        user = request.user
        print(user)
        amount = request.data.get("amount")
        currency = request.data.get('currency', 'usd')
        plan = request.data.get('plan',)

        if not amount or amount <= 0:
            return Response({"error": "Invalid amount provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,  
                currency=currency,
                metadata={'user_id': user.id},
            )

            Payment.objects.create(
                user=user,
                amount=amount,
                currency=currency,
                stripe_payment_intent_id=intent['id'],
                plan=plan,
                status=Payment.STATUS_TYPE.CREATED
            )

            return Response({'client_secret': intent['client_secret']}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.headers.get('Stripe-Signature')
        endpoint_secret = 'whsec_27b9225a2a8a147385be2501f6cc3dc0479ce84502598ab05e93e81fbfd1e92f'  

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            return JsonResponse({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError:
            return JsonResponse({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        # Handle specific event types
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            payment_intent_id = session.get("payment_intent")
            payment = Payment.objects.filter(stripe_payment_intent_id=payment_intent_id)

            if payment and payment.status != "SUCCEEDED":
                credit_user_based_on_plan(payment)

        return JsonResponse({'status': 'success'}, status=status.HTTP_200_OK)


class BkashSandboxPaymentView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        plan = request.data.get('plan')
        print(plan)
        amount = request.data.get("amount")
        if not amount:
            return Response({"error": "Amount are required"}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        try:
            merchant_invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
            print(merchant_invoice_number)
            payment_response = create_sandbox_payment_request(amount, merchant_invoice_number)
            payment_id = payment_response.get("paymentID")
             
            payment = Payment.objects.create(
                user=request.user,
                amount=amount,
                currency=Payment.CURRENCY_TYPE.BDT,
                status=Payment.STATUS_TYPE.PENDING,
                plan=plan,
                bkash_request_id=payment_id
            )

            return Response(payment_response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BkashExecutePaymentView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        payment_id = request.data.get("paymentID")
        
        if not payment_id:
            return Response({"error": "Payment id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            execution_response = excute_sandbox_payment(payment_id)
            # print("Execution Response", execution_response)
            payment = Payment.objects.get(bkash_request_id=payment_id)
            if execution_response.get("transactionStatus") == "Completed" or execution_response.get("statusCode") == '2062':
                if payment.status == payment.STATUS_TYPE.SUCCEEDED:
                    return Response({"message": "Payment already processed"}, status=status.HTTP_200_OK)
                
                payment.bkash_transaction_id = payment_id
                credit_user_based_on_plan(payment)
                payment.save()

                return Response({"message": "Payment executed successfully", "data": execution_response}, status=status.HTTP_200_OK)
            elif execution_response.get("transactionStatus") == "Initiated":
                payment.bkash_transaction_id = payment_id
                credit_user_based_on_plan(payment)
                payment.save()

                return Response({"message": "Payment executed successfully", "data": execution_response}, status=status.HTTP_200_OK)
            elif execution_response.get("transactionStatus") == "Declined":
                payment.status = payment.STATUS_TYPE.FAILED
                payment.save()
                return Response({"error": "Payment execution failed", "data": execution_response}, status=status.HTTP_400_BAD_REQUEST)
            elif execution_response.get("transactionStatus") == "Cancelled":
                payment.status = payment.STATUS_TYPE.CANCELED
                payment.save()
                return Response({"error": "Payment execution failed", "data": execution_response}, status=status.HTTP_408_REQUEST_TIMEOUT)
        
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class BkashQueryPaymentStatusView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        payment_id = request.data.get('paymentID')
        try:
            status_response = query_sandbox_payment_status(payment_id)
            
            payment = Payment.objects.get(bkash_request_id=payment_id)
            if status_response.get("transactionStatus") == "Completed":
                
                if payment.status == payment.STATUS_TYPE.SUCCEEDED:
                    return Response({"message": "Payment Already processed", 
                                     "data": status_response},
                                    status=status.HTTP_200_OK
                                    )
                
                return Response({"message": "Payment is not processed", 
                                 "data": status_response}, 
                                status=status.HTTP_402_PAYMENT_REQUIRED)
                
            elif status_response.get("transactionStatus") == "Initiated":
                return Response({"message": "Payment is not processed", 
                                 "data": status_response}, 
                                status=status.HTTP_402_PAYMENT_REQUIRED)
            else:
                return Response({"status": "Pending", "data": status_response}, 
                                status=status.HTTP_200_OK)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, 
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def bkashCallBack(request):
    status = request.GET.get("status")
    payment_id = request.GET.get("paymentID")

    if status == "success":
        return redirect(f"https://dashboard.peollo.io/payment-excution?payment_id={payment_id}")
    elif status == "failure":
        return redirect("https://dashboard.peollo.io/payment-failed")
    elif status == "cancel":
        return redirect("https://dashboard.peollo.io/payment-canceled")


class PaymentHistoryView(generics.ListAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializers
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        return Response(response.data, status=status.HTTP_200_OK)


class DestroyPaymentHistoryView(generics.DestroyAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializers
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)