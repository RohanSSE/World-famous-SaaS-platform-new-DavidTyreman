from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Role, Permission, Dashboard, Agency



@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    """Custom admin for Agency model"""
    
    list_display = (
        'id',
        'name', 
        'owner_email',
        'members_count',
        'sessions_count',
        'is_active_badge', 
        'created_at'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'owner__email', 'description')
    ordering = ('name',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'owner', 'description', 'website', 'phone_number', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def owner_email(self, obj):
        return obj.owner.email if obj.owner else '-'
    owner_email.short_description = 'Owner'
    
    def members_count(self, obj):
        count = obj.users.count()
        return format_html(
            '<span style="background-color: #e3f2fd; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    members_count.short_description = 'Members'
    
    def sessions_count(self, obj):
        count = obj.assigned_sessions.count()
        return format_html(
            '<span style="background-color: #f3e5f5; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    sessions_count.short_description = 'Sessions'
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">●</span> Active')
        return format_html('<span style="color: red; font-weight: bold;">●</span> Inactive')
    is_active_badge.short_description = 'Status'





@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model"""
    
    model = User
    list_display = (
        'email', 
        'role_name', 
        'agency_name', 
        'is_active_badge', 
        'is_staff', 
        'created_at'
    )
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('email', 'agency_name', 'phone_number')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        ('Personal Info', {
            'fields': ('role', 'agency', 'phone_number') 
        }),
        ('Permissions', {
            'fields': (
                'is_active', 
                'is_staff', 
                'is_superuser', 
                'groups', 
                'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 
                'password1', 
                'password2', 
                'role', 
                'agency',
                'phone_number',
                'is_active', 
                'is_staff'
            )
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined')
    
    def role_name(self, obj):
        """Display role name"""
        return obj.role.name if obj.role else '-'
    role_name.short_description = 'Role'
    role_name.admin_order_field = 'role__name'
    
    def is_active_badge(self, obj):
        """Display active status with colored badge"""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">●</span> Active'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">●</span> Inactive'
        )
    is_active_badge.short_description = 'Status'
    is_active_badge.admin_order_field = 'is_active'


    def agency_name(self, obj):
        """Display agency name"""
        return obj.agency.name if obj.agency else '-'
    agency_name.short_description = 'Agency'
    agency_name.admin_order_field = 'agency__name'



@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Custom admin for Role model"""
    
    list_display = (
        'name', 
        'description_short', 
        'permissions_count',
        'dashboards_count', 
        'users_count',
        'is_active_badge',
        'created_at'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)
    ordering = ('name',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Permissions', {
            'fields': ('permissions',),
            'description': 'Select permissions for this role'
        }),
        ('Dashboards', {  # New section
            'fields': ('dashboards',),
            'description': 'Select dashboards accessible to this role'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of roles to avoid breaking user access"""
        return False
    
    def description_short(self, obj):
        """Display truncated description"""
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'
    description_short.short_description = 'Description'
    
    def permissions_count(self, obj):
        """Display count of permissions"""
        count = obj.permissions.count()
        return format_html(
            '<span style="background-color: #e3f2fd; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    permissions_count.short_description = 'Permissions'
    
    def users_count(self, obj):
        """Display count of users with this role"""
        count = obj.users.count()
        return format_html(
            '<span style="background-color: #f3e5f5; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    users_count.short_description = 'Users'
    
    def dashboards_count(self, obj):
        """New: Display count of dashboards for this role"""
        count = obj.dashboards.count()
        return format_html(
            '<span style="background-color: #e8f5e8; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    dashboards_count.short_description = 'Dashboards'


    def is_active_badge(self, obj):
        """Display active status with colored badge"""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">●</span> Active'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">●</span> Inactive'
        )
    is_active_badge.short_description = 'Status'
    is_active_badge.admin_order_field = 'is_active'


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Custom admin for Permission model"""
    
    list_display = (
        'codename', 
        'name', 
        'description_short',
        'roles_count',
        'created_at'
    )
    list_filter = ('created_at',)
    search_fields = ('codename', 'name', 'description')
    ordering = ('codename',)
    
    fieldsets = (
        (None, {
            'fields': ('codename', 'name', 'description')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def description_short(self, obj):
        """Display truncated description"""
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'
    description_short.short_description = 'Description'
    
    def roles_count(self, obj):
        """Display count of roles using this permission"""
        count = obj.roles.count()
        return format_html(
            '<span style="background-color: #fff3e0; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    roles_count.short_description = 'Used by Roles'




@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    """Custom admin for Dashboard model"""
    
    list_display = (
        'code', 
        'name', 
        'description_short',
        'is_active_badge',
        'roles_count',  # New: Count of roles with access
        'created_at'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description', 'code')
    ordering = ('code',)
    
    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'description', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at',)
    
    def description_short(self, obj):
        """Display truncated description"""
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'
    description_short.short_description = 'Description'
    
    def roles_count(self, obj):
        """New: Display count of roles with access to this dashboard"""
        count = obj.roles.count()
        return format_html(
            '<span style="background-color: #f0f4c3; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    roles_count.short_description = 'Roles with Access'
    
    def is_active_badge(self, obj):
        """Display active status with colored badge"""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">●</span> Active'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">●</span> Inactive'
        )
    is_active_badge.short_description = 'Status'
    is_active_badge.admin_order_field = 'is_active'



# Customize admin site headers
admin.site.site_header = "User Management Admin"
admin.site.site_title = "User Management"
admin.site.index_title = "Welcome to User Management System"