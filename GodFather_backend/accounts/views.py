from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    RoleSerializer,
    PermissionSerializer,
    AgencySerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    LoginSerializer,
    ChangePasswordSerializer
)
from .models import Role, Permission, Agency
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

    # Authenticate user
    user = authenticate(request, username=email, password=password)
    
    if not user:
        return Response(
            {"detail": "Invalid email or password"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    user = User.objects.select_related("role", "agency").get(pk=user.pk)

    if not is_user_effectively_active(user):
        role_name = (user.role.name if user.role else "") or ""
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