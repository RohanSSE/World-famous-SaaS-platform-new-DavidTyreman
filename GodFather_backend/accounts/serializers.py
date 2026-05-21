from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Role, Permission, Dashboard
from .models import Agency


User = get_user_model()


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for Permission model"""
    
    class Meta:
        model = Permission
        fields = ['id', 'codename', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']



class DashboardSerializer(serializers.ModelSerializer):
    """New: Serializer for Dashboard model"""
    
    class Meta:
        model = Dashboard
        fields = ['id', 'code', 'name', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model with nested permissions"""
    
    permissions = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        required=False
    )
    permissions_details = PermissionSerializer(
        source='permissions', 
        read_only=True, 
        many=True
    )
    dashboards = serializers.PrimaryKeyRelatedField(  # New: Added for create/update
        many=True,
        queryset=Dashboard.objects.all(),
        required=False
    )
    dashboards_details = DashboardSerializer(  # New: Added read-only nested for display
        source='dashboards', 
        read_only=True, 
        many=True
    )
    users_count = serializers.SerializerMethodField()
    

    class Meta:
        model = Role
        fields = [
            'id', 
            'name', 
            'description', 
            'is_active',
            'permissions', 
            'permissions_details',
            'dashboards',  # New: For create/update
            'dashboards_details',  # New: Read-only nested for display
            'users_count',
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_users_count(self, obj):
        """Return count of users with this role"""
        return obj.users.count()

    def validate_name(self, value):
        """Validate role name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Role name cannot be empty.")
        return value.strip().lower()

    def create(self, validated_data):
        """Create role with permissions"""
        permissions_data = validated_data.pop('permissions', [])
        dashboards_data = validated_data.pop('dashboards', [])
        role = Role.objects.create(**validated_data)
        role.permissions.set(permissions_data)
        role.dashboards.set(dashboards_data)
        return role

    def update(self, instance, validated_data):
        """Update role with permissions"""
        permissions_data = validated_data.pop('permissions', None)
        dashboards_data = validated_data.pop('dashboards', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if permissions_data is not None:
            instance.permissions.set(permissions_data)
        if dashboards_data is not None:  # New
            instance.dashboards.set(dashboards_data)
        
        return instance


class AgencySerializer(serializers.ModelSerializer):
    """Serializer for Agency model"""
    
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    members_count = serializers.SerializerMethodField()
    sessions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Agency
        fields = ['id', 'name', 'owner', 'owner_email', 'description', 'website', 
                  'phone_number', 'is_active', 'members_count', 'sessions_count', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_members_count(self, obj):
        return obj.users.filter(is_active=True).count()
    
    def get_sessions_count(self, obj):
        return obj.assigned_sessions.count()



class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (read/update)"""
    
    # role_details = RoleSerializer(source='role', read_only=True)
    # agency_details = AgencySerializer(source='agency', read_only=True)
    permissions = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 
            'email', 
            'role',
            'role_name',
            # 'role_details',
            'agency',  # ADD THIS
            # 'agency_details',  # ADD THIS
            'phone_number',
            'is_active',
            'permissions',
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'email', 'created_at', 'updated_at']

    def get_permissions(self, obj):
        """Return user's permissions through their role"""
        return obj.get_all_permissions()

    def get_role_name(self, obj):
        return obj.role.name if obj.role else None


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    role = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.filter(is_active=True),
        required=False,
        allow_null=True
    )
    agency = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.filter(is_active=True), 
        required=False, 
        allow_null=True
        )  # ADD THIS

    class Meta:
        model = User
        fields = [
            'email', 
            'password', 
            'confirm_password', 
            'role', 
            'agency',
            'phone_number'
        ]

    def validate_email(self, value):
        """Validate email is unique"""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_password(self, value):
        """Validate password strength using Django's validators"""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "Password fields didn't match."
            })
        return attrs

    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        email = validated_data.pop('email')
        
        # Delegate to custom manager (auto-sets role based on agency)
        user = User.objects.create_user(
            email=email,
            password=password,
            **validated_data  # Includes agency, phone_number, role (if manually provided, but manager will overwrite based on agency)
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate_email(self, value):
        """Normalize email"""
        return value.lower()


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Normalize email"""
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )

    def validate_new_password(self, value):
        """Validate password strength"""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "Password fields didn't match."
            })
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for authenticated user password change"""
    
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )

    def validate_new_password(self, value):
        """Validate password strength"""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """Validate that new passwords match"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "Password fields didn't match."
            })
        return attrs


