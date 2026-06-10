from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timezone as datetime_timezone
import json

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    RoleSerializer,
    PermissionSerializer,
    AgencySerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
)
from .models import Role, Permission, Agency, SubscriptionPlan, UserSubscription
from .agency_utils import ensure_agency_for_user
from .status_utils import is_user_effectively_active
from .permissions import (
    HasRolePermission,
    require_permissions,
    can_view_user_directory,
    can_view_agency_directory,
    can_update_user_record,
    can_update_agency_record,
)


User = get_user_model()


# =====================================================
# AUTHENTICATION VIEWS
# =====================================================

@swagger_auto_schema(
    method='post',
    request_body=RegisterSerializer,
    responses={
        201: openapi.Response('User created successfully', UserSerializer),
        400: 'Validation error'
    },
    operation_description="Register a new user with email, password, and optional role"
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user"""
    user_type = request.data.get('user_type', 'user')  # "user", "agency", or "admin"
    if user_type == 'agency':
        role_name = 'agency'
    elif user_type == 'admin':
        role_name = 'admin'
    else:
        role_name = 'client'
    role, _ = Role.objects.get_or_create(name=role_name, defaults={'description': f'Role: {role_name}'})

    serializer = RegisterSerializer(
        data=request.data,
        context={'user_type': user_type, 'role': role},
    )
    serializer.is_valid(raise_exception=True)

    user = serializer.save()

    if role_name == 'agency':
        # Enforce pending state (user + agency org) until admin activates
        User.objects.filter(pk=user.pk).update(is_active=False, role=role)
        user.refresh_from_db()
        ensure_agency_for_user(user)
        agency = user.agency
        if agency:
            Agency.objects.filter(pk=agency.pk).update(
                is_active=False,
                approved_at=None,
            )
        return Response(
            {
                'message': 'Agency registered successfully. An admin must activate your account before you can sign in.',
                'user': UserSerializer(user).data,
                'pending_approval': True,
            },
            status=status.HTTP_201_CREATED,
        )

    if role_name == 'admin':
        user.is_staff = True
    user.save(update_fields=['role', 'is_staff'])

    # Generate JWT tokens so the user is logged in immediately (client / admin)
    refresh = RefreshToken.for_user(user)

    return Response(
        {
            'message': 'User registered successfully',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        },
        status=status.HTTP_201_CREATED
    )


@swagger_auto_schema(
    method='post',
    request_body=LoginSerializer,
    responses={
        200: openapi.Response(
            'Login successful',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    'access': openapi.Schema(type=openapi.TYPE_STRING),
                    'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                }
            )
        ),
        401: 'Invalid credentials',
        403: 'Account deactivated'
    },
    operation_description="Login with email and password to get JWT tokens"
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_with_email(request):
    """Authenticate user and return JWT tokens"""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']

    user = User.objects.filter(email__iexact=email).select_related("role", "agency").first()

    if not user or not user.check_password(password):
        return Response(
            {"detail": "Invalid email or password"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    role_name = (user.role.name if user.role else "") or ""
    if role_name.lower() == "agency" and user.agency and user.agency.is_active:
        update_user_fields = []
        update_agency_fields = []
        if not user.is_active:
            user.is_active = True
            update_user_fields.append("is_active")
        if user.agency.approved_at is None:
            user.agency.approved_at = timezone.now()
            update_agency_fields.append("approved_at")
        if update_user_fields:
            user.save(update_fields=update_user_fields)
        if update_agency_fields:
            user.agency.save(update_fields=update_agency_fields)

    if not is_user_effectively_active(user):
        if role_name.lower() == "agency":
            return Response(
                {
                    "detail": "Your agency account is pending admin approval. Please contact support or wait for activation.",
                    "code": "agency_pending_approval",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(
            {"detail": "User account is deactivated"},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    
    return Response({
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": UserSerializer(user).data
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    methods=['get'],
    responses={200: UserSerializer},
    operation_description="Get current authenticated user details"
)
@swagger_auto_schema(
    methods=['put', 'patch'],
    request_body=UserSerializer,
    responses={
        200: UserSerializer,
        400: 'Validation error'
    },
    operation_description="Update current authenticated user details"
)
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def me(request):
    """Get or update current user profile"""
    if request.method == 'GET':
        user = User.objects.select_related("role", "agency").get(pk=request.user.pk)
        return Response(UserSerializer(user).data)
    
    # Update user profile
    partial = request.method == 'PATCH'
    serializer = UserSerializer(request.user, data=request.data, partial=partial)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    
    return Response(serializer.data)


def _frontend_url(path):
    base = getattr(settings, 'FRONTEND_APP_URL', 'http://127.0.0.1:5173').rstrip('/')
    return f"{base}{path}"


def _env_file_value(name):
    env_path = os.path.join(getattr(settings, 'BASE_DIR', ''), '.env')
    if not os.path.exists(env_path):
        return ''
    try:
        with open(env_path, encoding='utf-8-sig') as env_file:
            for line in env_file:
                raw = line.strip()
                if not raw or raw.startswith('#') or '=' not in raw:
                    continue
                key, value = raw.split('=', 1)
                if key.strip() == name:
                    return value.strip().strip('"').strip("'")
    except OSError:
        return ''
    return ''


def _valid_stripe_secret_key(value):
    return bool(value and value.startswith('sk_') and 'your_secret_key_here' not in value)


def _stripe_client():
    try:
        import stripe
    except ImportError as exc:
        raise RuntimeError("Stripe package is not installed. Run pip install -r requirements.txt.") from exc

    secret_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
    if not _valid_stripe_secret_key(secret_key):
        secret_key = _env_file_value('STRIPE_SECRET_KEY')
    if not _valid_stripe_secret_key(secret_key):
        raise RuntimeError("STRIPE_SECRET_KEY is not configured in .env.")
    stripe.api_key = secret_key
    return stripe


def _stripe_value(obj, key, default=None):
    if obj is None:
        return default
    if hasattr(obj, 'get'):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _timestamp_to_datetime(value):
    if not value:
        return None
    return datetime.fromtimestamp(int(value), tz=datetime_timezone.utc)


def _datetime_iso(value):
    return value.isoformat() if value else None


def _stripe_amount_display(amount, currency):
    if amount in (None, ''):
        return ''
    try:
        return f"{str(currency or '').upper()} {int(amount) / 100:.2f}"
    except (TypeError, ValueError):
        return ''


def _account_type_for_user(user):
    role_name = (user.get_role_name() or '').lower()
    return 'agency' if role_name == 'agency' else 'user'


def _stripe_payment_document(subscription, stripe=None):
    document = {
        'stripe_checkout_session_id': subscription.stripe_checkout_session_id,
        'stripe_subscription_id': subscription.stripe_subscription_id,
        'stripe_payment_intent_id': subscription.stripe_payment_intent_id,
        'payment_status': '',
        'amount_total': None,
        'amount_paid': None,
        'currency': subscription.plan.currency,
        'amount_display': '',
        'invoice_id': '',
        'invoice_number': '',
        'invoice_status': '',
        'hosted_invoice_url': '',
        'invoice_pdf': '',
        'receipt_url': '',
        'paid_at': None,
        'stripe_error': '',
    }

    if not stripe:
        return document

    try:
        checkout_session = None
        if subscription.stripe_checkout_session_id:
            checkout_session = stripe.checkout.Session.retrieve(
                subscription.stripe_checkout_session_id,
                expand=['invoice', 'payment_intent', 'payment_intent.latest_charge'],
            )
            document['payment_status'] = _stripe_value(checkout_session, 'payment_status', '') or ''
            document['amount_total'] = _stripe_value(checkout_session, 'amount_total')
            document['currency'] = _stripe_value(checkout_session, 'currency', document['currency']) or document['currency']
            document['paid_at'] = _datetime_iso(_timestamp_to_datetime(_stripe_value(checkout_session, 'created')))

        invoice = _stripe_value(checkout_session, 'invoice') if checkout_session else None
        if isinstance(invoice, str):
            invoice = stripe.Invoice.retrieve(invoice)
        elif not invoice and subscription.stripe_subscription_id:
            invoices = stripe.Invoice.list(subscription=subscription.stripe_subscription_id, limit=1)
            invoice_items = _stripe_value(invoices, 'data', []) or []
            invoice = invoice_items[0] if invoice_items else None

        if invoice:
            document['invoice_id'] = _stripe_value(invoice, 'id', '') or ''
            document['invoice_number'] = _stripe_value(invoice, 'number', '') or ''
            document['invoice_status'] = _stripe_value(invoice, 'status', '') or ''
            document['hosted_invoice_url'] = _stripe_value(invoice, 'hosted_invoice_url', '') or ''
            document['invoice_pdf'] = _stripe_value(invoice, 'invoice_pdf', '') or ''
            document['amount_paid'] = _stripe_value(invoice, 'amount_paid')
            document['currency'] = _stripe_value(invoice, 'currency', document['currency']) or document['currency']
            status_transitions = _stripe_value(invoice, 'status_transitions', {}) or {}
            document['paid_at'] = _datetime_iso(
                _timestamp_to_datetime(_stripe_value(status_transitions, 'paid_at'))
            ) or document['paid_at']

        payment_intent = _stripe_value(checkout_session, 'payment_intent') if checkout_session else None
        if isinstance(payment_intent, str):
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent, expand=['latest_charge'])
        elif not payment_intent and subscription.stripe_payment_intent_id:
            payment_intent = stripe.PaymentIntent.retrieve(subscription.stripe_payment_intent_id, expand=['latest_charge'])

        if payment_intent:
            document['stripe_payment_intent_id'] = _stripe_value(payment_intent, 'id', document['stripe_payment_intent_id']) or ''
            document['payment_status'] = document['payment_status'] or _stripe_value(payment_intent, 'status', '') or ''
            document['amount_total'] = document['amount_total'] or _stripe_value(payment_intent, 'amount')
            document['amount_paid'] = document['amount_paid'] or _stripe_value(payment_intent, 'amount_received')
            document['currency'] = _stripe_value(payment_intent, 'currency', document['currency']) or document['currency']
            charge = _stripe_value(payment_intent, 'latest_charge')
            if isinstance(charge, str):
                charge = stripe.Charge.retrieve(charge)
            if charge:
                document['receipt_url'] = _stripe_value(charge, 'receipt_url', '') or ''
                document['paid_at'] = document['paid_at'] or _datetime_iso(_timestamp_to_datetime(_stripe_value(charge, 'created')))

        amount = document['amount_paid'] if document['amount_paid'] not in (None, '') else document['amount_total']
        document['amount_display'] = _stripe_amount_display(amount, document['currency'])
    except Exception as exc:
        document['stripe_error'] = str(exc)

    return document


def _subscription_history_item(subscription, stripe=None, include_user=False):
    document = _stripe_payment_document(subscription, stripe=stripe)
    user = subscription.user
    item = {
        'id': subscription.id,
        'status': subscription.status,
        'is_active': subscription.is_active,
        'plan': SubscriptionPlanSerializer(subscription.plan).data,
        'current_period_end': _datetime_iso(subscription.current_period_end),
        'created_at': _datetime_iso(subscription.created_at),
        'updated_at': _datetime_iso(subscription.updated_at),
        'payment': document,
    }
    if include_user:
        item['user'] = {
            'id': user.id,
            'email': user.email,
            'role_name': user.get_role_name(),
            'account_type': _account_type_for_user(user),
            'agency_id': user.agency_id,
            'agency_name': user.agency.name if user.agency else None,
        }
    return item


def _stripe_or_none():
    try:
        return _stripe_client(), ''
    except RuntimeError as exc:
        return None, str(exc)


def _latest_active_subscription(user):
    now = timezone.now()
    return user.subscriptions.select_related('plan').filter(
        status__in=[UserSubscription.STATUS_ACTIVE, UserSubscription.STATUS_TRIALING],
    ).filter(
        models.Q(current_period_end__isnull=True) | models.Q(current_period_end__gt=now)
    ).order_by('-updated_at').first()


def _subscription_payload(user):
    plan = SubscriptionPlan.active_plan()
    subscription = _latest_active_subscription(user)
    return {
        'has_active_subscription': bool(user.has_active_subscription()),
        'plan': SubscriptionPlanSerializer(plan).data if plan else None,
        'subscription': UserSubscriptionSerializer(subscription).data if subscription else None,
        'stripe_publishable_key': getattr(settings, 'STRIPE_PUBLISHABLE_KEY', ''),
    }


def _can_manage_subscription_plans(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    return bool(user.has_role('admin') or user.has_perm_codename('billing.update'))


@swagger_auto_schema(
    methods=['get'],
    responses={200: SubscriptionPlanSerializer(many=True)},
    operation_description="List subscription plans for admin billing settings"
)
@swagger_auto_schema(
    methods=['post'],
    request_body=SubscriptionPlanSerializer,
    responses={201: SubscriptionPlanSerializer},
    operation_description="Create a subscription plan for Stripe checkout"
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def subscription_plans(request):
    if not _can_manage_subscription_plans(request.user):
        return Response({'detail': 'You do not have permission to manage subscription plans.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        plans = SubscriptionPlan.objects.all().order_by('display_order', 'id')
        return Response(SubscriptionPlanSerializer(plans, many=True).data)

    serializer = SubscriptionPlanSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    methods=['get'],
    responses={200: SubscriptionPlanSerializer},
    operation_description="Get a subscription plan"
)
@swagger_auto_schema(
    methods=['put', 'patch'],
    request_body=SubscriptionPlanSerializer,
    responses={200: SubscriptionPlanSerializer},
    operation_description="Update a subscription plan"
)
@swagger_auto_schema(
    methods=['delete'],
    responses={204: 'Subscription plan deleted'},
    operation_description="Delete a subscription plan"
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def subscription_plan_detail(request, pk):
    if not _can_manage_subscription_plans(request.user):
        return Response({'detail': 'You do not have permission to manage subscription plans.'}, status=status.HTTP_403_FORBIDDEN)

    plan = get_object_or_404(SubscriptionPlan, pk=pk)

    if request.method == 'GET':
        return Response(SubscriptionPlanSerializer(plan).data)

    if request.method in ['PUT', 'PATCH']:
        serializer = SubscriptionPlanSerializer(plan, data=request.data, partial=request.method == 'PATCH')
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    plan.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def _checkout_line_item(plan):
    if plan.stripe_price_id:
        return {'price': plan.stripe_price_id, 'quantity': 1}

    price_data = {
        'currency': plan.currency.lower(),
        'unit_amount': int(plan.price * 100),
        'product_data': {
            'name': plan.name,
            'description': plan.description or plan.name,
        },
    }
    if plan.billing_interval != SubscriptionPlan.INTERVAL_ONE_TIME:
        price_data['recurring'] = {'interval': plan.billing_interval}
    return {'price_data': price_data, 'quantity': 1}


def _sync_subscription_from_checkout_session(checkout_session):
    metadata = _stripe_value(checkout_session, 'metadata', {}) or {}
    user_id = metadata.get('user_id')
    plan_id = metadata.get('plan_id')
    checkout_session_id = _stripe_value(checkout_session, 'id', '')

    subscription = UserSubscription.objects.filter(
        stripe_checkout_session_id=checkout_session_id
    ).select_related('user', 'plan').first()

    if not subscription:
        if not user_id or not plan_id:
            return None
        try:
            user = User.objects.get(pk=user_id)
            plan = SubscriptionPlan.objects.get(pk=plan_id)
        except (User.DoesNotExist, SubscriptionPlan.DoesNotExist):
            return None
        subscription = UserSubscription.objects.create(
            user=user,
            plan=plan,
            stripe_checkout_session_id=checkout_session_id,
        )

    stripe_subscription = _stripe_value(checkout_session, 'subscription')
    stripe_payment_intent = _stripe_value(checkout_session, 'payment_intent')
    payment_status = _stripe_value(checkout_session, 'payment_status', '')
    mode = _stripe_value(checkout_session, 'mode', '')

    status_value = subscription.status
    current_period_end = subscription.current_period_end
    stripe_subscription_id = ''

    if isinstance(stripe_subscription, str):
        stripe_subscription_id = stripe_subscription
        try:
            stripe = _stripe_client()
            stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        except Exception:
            stripe_subscription = None

    if stripe_subscription:
        stripe_subscription_id = _stripe_value(stripe_subscription, 'id', stripe_subscription_id)
        status_value = _stripe_value(stripe_subscription, 'status', UserSubscription.STATUS_ACTIVE)
        current_period_end = _timestamp_to_datetime(_stripe_value(stripe_subscription, 'current_period_end'))
    elif mode == 'payment' and payment_status == 'paid':
        status_value = UserSubscription.STATUS_ACTIVE
        current_period_end = None
    elif payment_status == 'paid':
        status_value = UserSubscription.STATUS_ACTIVE

    subscription.status = status_value or UserSubscription.STATUS_INCOMPLETE
    subscription.stripe_customer_id = _stripe_value(checkout_session, 'customer', '') or subscription.stripe_customer_id
    subscription.stripe_subscription_id = stripe_subscription_id or subscription.stripe_subscription_id
    subscription.stripe_payment_intent_id = (
        stripe_payment_intent if isinstance(stripe_payment_intent, str) else _stripe_value(stripe_payment_intent, 'id', '')
    ) or subscription.stripe_payment_intent_id
    subscription.current_period_end = current_period_end
    subscription.save()
    return subscription


@swagger_auto_schema(
    method='get',
    responses={200: openapi.Response('Current subscription status')},
    operation_description="Get the active plan and current user's subscription status"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_status(request):
    user = User.objects.select_related('role').get(pk=request.user.pk)
    return Response(_subscription_payload(user))


@swagger_auto_schema(
    method='get',
    responses={200: openapi.Response('Current user subscription invoices and receipts')},
    operation_description="List current user's subscription payments with Stripe invoice/receipt links"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_invoices(request):
    subscriptions = UserSubscription.objects.filter(user=request.user).select_related(
        'user', 'user__role', 'user__agency', 'plan'
    ).order_by('-updated_at')
    stripe, stripe_error = _stripe_or_none()
    payments = [_subscription_history_item(subscription, stripe=stripe) for subscription in subscriptions]
    return Response({
        'payments': payments,
        'stripe_error': stripe_error,
    })


@swagger_auto_schema(
    method='get',
    responses={200: openapi.Response('Admin subscription subscribers with payment details')},
    operation_description="Admin: list all subscribers and their Stripe invoice/receipt links"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_subscribers(request):
    if not _can_manage_subscription_plans(request.user):
        return Response({'detail': 'You do not have permission to view subscribers.'}, status=status.HTTP_403_FORBIDDEN)

    subscriptions = UserSubscription.objects.select_related(
        'user', 'user__role', 'user__agency', 'plan'
    ).order_by('-updated_at')[:200]
    stripe, stripe_error = _stripe_or_none()
    subscribers = [
        _subscription_history_item(subscription, stripe=stripe, include_user=True)
        for subscription in subscriptions
    ]
    return Response({
        'subscribers': subscribers,
        'total': len(subscribers),
        'stripe_error': stripe_error,
    })


@swagger_auto_schema(
    method='post',
    responses={200: openapi.Response('Stripe checkout session')},
    operation_description="Create a Stripe checkout session for the active subscription plan"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_subscription_checkout(request):
    user = User.objects.select_related('role').get(pk=request.user.pk)
    if user.has_active_subscription():
        return Response({'already_active': True, **_subscription_payload(user)})

    plan = SubscriptionPlan.active_plan()
    if not plan:
        return Response({'detail': 'No active subscription plan is configured.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        stripe = _stripe_client()
    except RuntimeError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    success_url = request.data.get('success_url') or _frontend_url('/phase-complete/1?checkout=success&session_id={CHECKOUT_SESSION_ID}')
    cancel_url = request.data.get('cancel_url') or _frontend_url('/phase-complete/1?checkout=cancel')
    checkout_mode = 'payment' if plan.billing_interval == SubscriptionPlan.INTERVAL_ONE_TIME else 'subscription'

    checkout_kwargs = {
        'mode': checkout_mode,
        'line_items': [_checkout_line_item(plan)],
        'success_url': success_url,
        'cancel_url': cancel_url,
        'customer_email': user.email,
        'client_reference_id': str(user.id),
        'metadata': {
            'user_id': str(user.id),
            'plan_id': str(plan.id),
        },
    }
    if checkout_mode == 'subscription':
        checkout_kwargs['subscription_data'] = {
            'metadata': {
                'user_id': str(user.id),
                'plan_id': str(plan.id),
            }
        }

    try:
        checkout_session = stripe.checkout.Session.create(**checkout_kwargs)
    except Exception as exc:
        return Response({'detail': f'Stripe checkout failed: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)

    UserSubscription.objects.update_or_create(
        user=user,
        plan=plan,
        stripe_checkout_session_id=checkout_session.id,
        defaults={
            'status': UserSubscription.STATUS_INCOMPLETE,
            'stripe_customer_id': _stripe_value(checkout_session, 'customer', '') or '',
        },
    )

    return Response({
        'checkout_session_id': checkout_session.id,
        'checkout_url': checkout_session.url,
        'plan': SubscriptionPlanSerializer(plan).data,
    })


@swagger_auto_schema(
    method='post',
    responses={200: openapi.Response('Verified subscription status')},
    operation_description="Verify a Stripe checkout session after redirect"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_subscription_checkout(request):
    checkout_session_id = request.data.get('checkout_session_id') or request.data.get('session_id')
    if not checkout_session_id:
        return Response({'detail': 'checkout_session_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        stripe = _stripe_client()
        checkout_session = stripe.checkout.Session.retrieve(
            checkout_session_id,
            expand=['subscription', 'payment_intent'],
        )
    except RuntimeError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as exc:
        return Response({'detail': f'Unable to verify checkout: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)

    subscription = _sync_subscription_from_checkout_session(checkout_session)
    if not subscription or subscription.user_id != request.user.id:
        return Response({'detail': 'Checkout session does not belong to this user.'}, status=status.HTTP_403_FORBIDDEN)

    user = User.objects.select_related('role').get(pk=request.user.pk)
    return Response(_subscription_payload(user))


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    payload = request.body
    signature = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')

    try:
        stripe = _stripe_client()
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
        else:
            event = json.loads(payload.decode('utf-8'))
    except Exception as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    event_type = _stripe_value(event, 'type')
    data_object = _stripe_value(_stripe_value(event, 'data', {}), 'object', {})

    if event_type in {'checkout.session.completed', 'checkout.session.async_payment_succeeded'}:
        _sync_subscription_from_checkout_session(data_object)
    elif event_type in {'customer.subscription.updated', 'customer.subscription.deleted'}:
        stripe_subscription_id = _stripe_value(data_object, 'id', '')
        subscription = UserSubscription.objects.filter(stripe_subscription_id=stripe_subscription_id).first()
        if subscription:
            subscription.status = _stripe_value(data_object, 'status', UserSubscription.STATUS_CANCELED)
            subscription.current_period_end = _timestamp_to_datetime(_stripe_value(data_object, 'current_period_end'))
            subscription.save(update_fields=['status', 'current_period_end', 'updated_at'])

    return Response({'received': True})


@swagger_auto_schema(
    method='post',
    request_body=ChangePasswordSerializer,
    responses={
        200: 'Password changed successfully',
        400: 'Validation error or incorrect old password'
    },
    operation_description="Change password for authenticated user"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change password for authenticated user"""
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = request.user
    old_password = serializer.validated_data['old_password']
    new_password = serializer.validated_data['new_password']
    
    # Check if old password is correct
    if not user.check_password(old_password):
        return Response(
            {"old_password": "Incorrect password"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    return Response(
        {"message": "Password changed successfully"},
        status=status.HTTP_200_OK
    )


# =====================================================
# PASSWORD RESET VIEWS
# =====================================================

@swagger_auto_schema(
    method='post',
    request_body=PasswordResetSerializer,
    responses={
        200: 'Password reset email sent (if email exists)'
    },
    operation_description="Request password reset email"
)
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """Request password reset via email"""
    serializer = PasswordResetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data['email']
    
    try:
        user = User.objects.get(email__iexact=email, is_active=True)
    except User.DoesNotExist:
        # Return success message even if user doesn't exist (security)
        return Response(
            {"message": "If the email exists, a password reset link has been sent"},
            status=status.HTTP_200_OK
        )

    # Generate password reset token
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    
    # Build reset URL
    current_site = get_current_site(request)
    frontend_site = getattr(settings, 'FRONTEND_BASE_URL', current_site.domain)
    protocol = 'https' if request.is_secure() else 'http'
    
    # You can customize this to point to your React frontend
    reset_url = f"{protocol}://{frontend_site}/reset-password/{uid}/{token}/"
    
    # Render email template
    context = {
        'user': user,
        'domain': current_site.domain,
        'uid': uid,
        'token': token,
        'protocol': protocol,
        'reset_url': reset_url,
    }
    
    html_message = render_to_string('password_reset_email.html', context)
    plain_message = f"Hello {user.email},\n\nPlease use the following link to reset your password:\n{reset_url}\n\nIf you did not request this, please ignore this email."
    
    # Send email
    send_mail(
        subject="Password Reset Request",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )
    
    return Response(
        {"message": "If the email exists, a password reset link has been sent"},
        status=status.HTTP_200_OK
    )


@swagger_auto_schema(
    method='post',
    request_body=PasswordResetConfirmSerializer,
    responses={
        200: 'Password has been reset successfully',
        400: 'Invalid link or token'
    },
    operation_description="Confirm password reset with token"
)
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """Confirm password reset with token"""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    uidb64 = serializer.validated_data['uid']
    token = serializer.validated_data['token']
    new_password = serializer.validated_data['new_password']

    # Decode user ID
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid, is_active=True)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {'detail': 'Invalid reset link'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify token
    if not default_token_generator.check_token(user, token):
        return Response(
            {'detail': 'Invalid or expired token'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Set new password
    user.set_password(new_password)
    user.save()
    
    return Response(
        {'message': 'Password has been reset successfully'},
        status=status.HTTP_200_OK
    )


# =====================================================
# ROLE MANAGEMENT VIEWS
# =====================================================

@swagger_auto_schema(
    methods=['get'],
    responses={
        200: openapi.Response('List of roles', RoleSerializer(many=True)),
        403: 'Forbidden'
    },
    operation_description="List all roles (requires 'roles.view' permission)"
)
@swagger_auto_schema(
    methods=['post'],
    request_body=RoleSerializer,
    responses={
        201: openapi.Response('Role created', RoleSerializer),
        400: 'Validation error',
        403: 'Forbidden'
    },
    operation_description="Create a new role (requires 'roles.create' permission)"
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def roles_list_create(request):
    """List all roles or create a new role"""
    
    if request.method == 'GET':
        # Check permission
        if not request.user.has_perm_codename('roles.view'):
            return Response(
                {"detail": "You do not have permission to view roles"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        roles = Role.objects.all()
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Check permission
        if not request.user.has_perm_codename('roles.create'):
            return Response(
                {"detail": "You do not have permission to create roles"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = RoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.save()
        
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


@swagger_auto_schema(
    methods=['get'],
    responses={200: RoleSerializer},
    operation_description="Get role details"
)
@swagger_auto_schema(
    methods=['put', 'patch'],
    request_body=RoleSerializer,
    responses={200: RoleSerializer},
    operation_description="Update role"
)
@swagger_auto_schema(
    methods=['delete'],
    responses={204: 'Role deleted'},
    operation_description="Delete role"
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, HasRolePermission])
def role_detail(request, pk):
    """Get, update or delete a role"""
    role = get_object_or_404(Role, pk=pk)
    
    if request.method == 'GET':
        if not request.user.has_perm_codename('roles.view'):
            return Response(
                {"detail": "You do not have permission to view roles"},
                status=status.HTTP_403_FORBIDDEN
            )
        return Response(RoleSerializer(role).data)
    
    elif request.method in ['PUT', 'PATCH']:
        if not request.user.has_perm_codename('roles.update'):
            return Response(
                {"detail": "You do not have permission to update roles"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = RoleSerializer(role, data=request.data, partial=request.method=='PATCH')
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        if not request.user.has_perm_codename('roles.delete'):
            return Response(
                {"detail": "You do not have permission to delete roles"},
                status=status.HTTP_403_FORBIDDEN
            )
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =====================================================
# PERMISSION MANAGEMENT VIEWS
# =====================================================

@swagger_auto_schema(
    methods=['get'],
    responses={200: openapi.Response('List of permissions', PermissionSerializer(many=True))},
    operation_description="List all permissions"
)
@swagger_auto_schema(
    methods=['post'],
    request_body=PermissionSerializer,
    responses={201: PermissionSerializer},
    operation_description="Create a new permission"
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def permissions_list_create(request):
    """List or create permissions"""
    if request.method == 'GET':
        if not request.user.has_perm_codename('permissions.view'):
            return Response(
                {"detail": "You do not have permission to view permissions"},
                status=status.HTTP_403_FORBIDDEN
            )
        permissions = Permission.objects.all()
        return Response(PermissionSerializer(permissions, many=True).data)
    
    elif request.method == 'POST':
        if not request.user.has_perm_codename('permissions.create'):
            return Response(
                {"detail": "You do not have permission to create permissions"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = PermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    methods=['get'],
    responses={200: PermissionSerializer},
    operation_description="Get permission details"
)
@swagger_auto_schema(
    methods=['put', 'patch'],
    request_body=PermissionSerializer,
    responses={200: PermissionSerializer},
    operation_description="Update permission"
)
@swagger_auto_schema(
    methods=['delete'],
    responses={204: 'Permission deleted'},
    operation_description="Delete permission"
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, HasRolePermission])
def permission_detail(request, pk):
    """Get, update or delete permission"""
    permission = get_object_or_404(Permission, pk=pk)
    
    if request.method == 'GET':
        if not request.user.has_perm_codename('permissions.view'):
            return Response(
                {"detail": "You do not have permission to view permissions"},
                status=status.HTTP_403_FORBIDDEN
            )
        return Response(PermissionSerializer(permission).data)
    
    elif request.method in ['PUT', 'PATCH']:
        if not request.user.has_perm_codename('permissions.update'):
            return Response(
                {"detail": "You do not have permission to update permissions"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = PermissionSerializer(permission, data=request.data, partial=request.method=='PATCH')
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        if not request.user.has_perm_codename('permissions.delete'):
            return Response(
                {"detail": "You do not have permission to delete permissions"},
                status=status.HTTP_403_FORBIDDEN
            )
        permission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =====================================================
# USER MANAGEMENT VIEWS
# =====================================================

@swagger_auto_schema(
    method='get',
    responses={200: openapi.Response('List of users', UserSerializer(many=True))},
    operation_description="List all users (requires 'users.view' permission)"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasRolePermission])
def users_list(request):
    """List all users"""
    if not can_view_user_directory(request.user):
        return Response(
            {"detail": "You do not have permission to view users"},
            status=status.HTTP_403_FORBIDDEN
        )
    users = User.objects.all().select_related('role', 'agency').order_by('-created_at')
    return Response(UserSerializer(users, many=True).data)


@swagger_auto_schema(
    methods=['get'],
    responses={200: UserSerializer},
    operation_description="Get user details"
)
@swagger_auto_schema(
    methods=['put', 'patch'],
    request_body=UserSerializer,
    responses={200: UserSerializer},
    operation_description="Update user"
)
@swagger_auto_schema(
    methods=['delete'],
    responses={204: 'User deleted'},
    operation_description="Delete user"
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, HasRolePermission])
def user_detail(request, pk):
    """Get, update or delete user"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'GET':
        if not can_view_user_directory(request.user):
            return Response(
                {"detail": "You do not have permission to view users"},
                status=status.HTTP_403_FORBIDDEN
            )
        return Response(UserSerializer(user).data)
    
    elif request.method in ['PUT', 'PATCH']:
        if not can_update_user_record(request.user):
            return Response(
                {"detail": "You do not have permission to update users"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = UserSerializer(user, data=request.data, partial=request.method=='PATCH')
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user.refresh_from_db()
        if user.role and user.role.name.lower() == 'agency':
            ensure_agency_for_user(user)
            agency = user.agency
            if agency:
                if user.is_active:
                    Agency.objects.filter(pk=agency.pk).update(
                        is_active=True,
                        approved_at=timezone.now(),
                    )
                else:
                    Agency.objects.filter(pk=agency.pk).update(
                        is_active=False,
                        approved_at=None,
                    )
        return Response(UserSerializer(user).data)
    
    elif request.method == 'DELETE':
        if not request.user.has_perm_codename('users.delete'):
            return Response(
                {"detail": "You do not have permission to delete users"},
                status=status.HTTP_403_FORBIDDEN
            )
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


    
# =====================================================
# AGENCY MANAGEMENT VIEWS
# =====================================================

@swagger_auto_schema(
    methods=['get'],
    responses={200: openapi.Response('List of agencies', AgencySerializer(many=True))},
    operation_description="List all agencies"
)
@swagger_auto_schema(
    methods=['post'],
    request_body=AgencySerializer,
    responses={201: AgencySerializer},
    operation_description="Create a new agency"
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def agencies_list_create(request):
    """List or create agencies"""
    if request.method == 'GET':
        if not can_view_agency_directory(request.user):
            return Response({"detail": "You do not have permission to view agencies"}, status=403)

        agencies = Agency.objects.all().select_related('owner').order_by('-created_at')
        return Response(AgencySerializer(agencies, many=True).data)
    
    elif request.method == 'POST':
        if not request.user.has_perm_codename('agencies.create'):
            return Response({"detail": "No permission"}, status=403)
        
        serializer = AgencySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    methods=['get'],
    responses={200: AgencySerializer},
    operation_description="Get agency details"
)
@swagger_auto_schema(
    methods=['put', 'patch'],
    request_body=AgencySerializer,
    responses={200: AgencySerializer},
    operation_description="Update agency"
)
@swagger_auto_schema(
    methods=['delete'],
    responses={204: 'Agency deleted'},
    operation_description="Delete agency"
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, HasRolePermission])
def agency_detail(request, pk):
    """Get, update or delete agency"""
    agency = get_object_or_404(Agency, pk=pk)
    
    if request.method == 'GET':
        if not can_view_agency_directory(request.user):
            return Response({"detail": "You do not have permission to view agencies"}, status=403)
        return Response(AgencySerializer(agency).data)
    
    elif request.method in ['PUT', 'PATCH']:
        # Allow global agency editors (admin/staff) OR the agency owner to update this record
        if not (can_update_agency_record(request.user) or agency.owner_id == request.user.id):
            # Fallback: allow activating/deactivating only (is_active) for users
            # who are allowed to view agencies in the admin panel.
            if can_view_agency_directory(request.user):
                allowed_keys = {"is_active"}
                incoming_keys = set((request.data or {}).keys())
                if incoming_keys.issubset(allowed_keys):
                    pass
                else:
                    return Response(
                        {"detail": "You do not have permission to update agencies"},
                        status=403,
                    )
            else:
                return Response(
                    {"detail": "You do not have permission to update agencies"},
                    status=403,
                )
        serializer = AgencySerializer(agency, data=request.data, partial=request.method == 'PATCH')
        serializer.is_valid(raise_exception=True)
        serializer.save()
        agency.refresh_from_db()
        if agency.is_active and agency.approved_at is None:
            agency.approved_at = timezone.now()
            agency.save(update_fields=['approved_at'])
        elif not agency.is_active and agency.approved_at is not None:
            agency.approved_at = None
            agency.save(update_fields=['approved_at'])

        if agency.owner_id:
            owner = agency.owner
            if agency.is_active and agency.approved_at:
                if not owner.is_active:
                    owner.is_active = True
                    owner.save(update_fields=['is_active'])
                ensure_agency_for_user(owner)
            elif owner.is_active:
                owner.is_active = False
                owner.save(update_fields=['is_active'])
        return Response(AgencySerializer(agency).data)
    
    elif request.method == 'DELETE':
        if not request.user.has_perm_codename('agencies.delete'):
            return Response({"detail": "No permission"}, status=403)
        agency.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)