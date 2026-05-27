from rest_framework.permissions import BasePermission
from functools import wraps
from rest_framework.response import Response
from rest_framework import status


class HasRolePermission(BasePermission):
    """
    Custom permission class to check if user has required role permissions.
    This is used as a base permission class with DRF views.
    """
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated and has an active role.
        Specific permission checks are done in the view using has_perm_codename.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers / Django staff always have permission
        if request.user.is_superuser or getattr(request.user, 'is_staff', False):
            return True

        # User must have an active role
        if not request.user.role or not request.user.role.is_active:
            return False

        return True


def _role_name(user):
    if not getattr(user, 'role', None):
        return ''
    return (user.role.name or '').lower()


def can_view_user_directory(user):
    """List all users — admin panel directory (read)."""
    if not user or not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser or getattr(user, 'is_staff', False):
        return True
    if _role_name(user) == 'admin':
        return True
    if user.has_perm_codename('users.view'):
        return True
    # Logged-in app users (client/agency) may open admin user list
    if _role_name(user) in ('client', 'agency'):
        return True
    return False


def can_view_agency_directory(user):
    """List all agencies — admin panel directory (read)."""
    if not user or not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser or getattr(user, 'is_staff', False):
        return True
    if _role_name(user) == 'admin':
        return True
    if user.has_perm_codename('agencies.view'):
        return True
    if _role_name(user) in ('client', 'agency', 'admin'):
        return True
    return False


def can_update_user_record(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or getattr(user, 'is_staff', False):
        return True
    role_name = _role_name(user)
    if role_name and 'admin' in role_name:
        return True
    return user.has_perm_codename('users.update')


def can_update_agency_record(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or getattr(user, 'is_staff', False):
        return True
    role_name = _role_name(user)
    # Be tolerant to naming variants (e.g. "superadmin", "super admin")
    if role_name and 'admin' in role_name:
        return True
    return user.has_perm_codename('agencies.update')


class IsAdminUser(BasePermission):
    """
    Permission class to check if user is admin/superuser
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


def require_permissions(*permission_codenames):
    """
    Decorator to check if user has specific permissions.
    Can be used with function-based views.
    
    Usage:
        @require_permissions('users.view', 'users.create')
        def my_view(request):
            # View code here
    
    Args:
        *permission_codenames: Variable number of permission codename strings
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {"detail": "Authentication credentials were not provided."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Superusers bypass permission checks
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Check if user has an active role
            if not request.user.role or not request.user.role.is_active:
                return Response(
                    {"detail": "You do not have an active role assigned."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check each required permission
            missing_permissions = []
            for perm_codename in permission_codenames:
                if not request.user.has_perm_codename(perm_codename):
                    missing_permissions.append(perm_codename)
            
            if missing_permissions:
                return Response(
                    {
                        "detail": "You do not have permission to perform this action.",
                        "missing_permissions": missing_permissions
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # User has all required permissions
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


class IsOwnerOrHasPermission(BasePermission):
    """
    Permission class that allows users to access their own objects
    or requires specific permission for other objects.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user is the owner of the object or has required permission.
        """
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user is the owner (for User objects)
        if hasattr(obj, 'id') and obj.id == request.user.id:
            return True
        
        # Check if user is related to the object
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # Check if view has a required_permission attribute
        if hasattr(view, 'required_permission'):
            return request.user.has_perm_codename(view.required_permission)
        
        return False