from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.utils import timezone

class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password"""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        # Handle superuser role (overrides auto-assign)
        if extra_fields.get('is_superuser', False):
            admin_role, _ = Role.objects.get_or_create(name='admin', defaults={'description': 'Administrator role'})
            user.role = admin_role
        else:
            # Auto-assign role based on agency (for regular users only)
            agency = extra_fields.get('agency')  # Could be None or Agency instance/PK
            if agency:
                role_name = 'agency'
            else:
                role_name = 'client'

            role, _ = Role.objects.get_or_create(name=role_name, defaults={'description': f'Role: {role_name}'})
            user.role = role


        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with an email and password"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class Permission(models.Model):
    """
    Custom permission model for granular access control
    """
    codename = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Format: app_label.action (e.g., 'roles.view', 'users.create')"
    )
    name = models.CharField(
        max_length=255,
        help_text="Human-readable permission name"
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['codename']
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'

    def __str__(self):
        return f"{self.name} ({self.codename})"



class Dashboard(models.Model):
    DASHBOARD_CHOICES = [
        ('tasks', 'Tasks'),
        ('reviews', 'Reviews'),
    ]

    code = models.CharField(max_length=50, choices=DASHBOARD_CHOICES, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name



class Role(models.Model):
    """
    Role model for grouping permissions
    """
    name = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Role name (e.g., 'admin', 'agency', 'client')"
    )
    description = models.TextField(blank=True, null=True)
    permissions = models.ManyToManyField(
        Permission, 
        blank=True,
        related_name='roles'
    )
    dashboards = models.ManyToManyField(
        Dashboard, 
        blank=True, 
        related_name="roles"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.name

    def get_permission_codenames(self):
        """Returns list of permission codenames for this role"""
        return list(self.permissions.values_list('codename', flat=True))




class Agency(models.Model):
    """Agency/Organization model for multi-tenant architecture"""
    name = models.CharField(max_length=255, unique=True)
    owner = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_agencies',
        help_text="Agency owner/admin"
    )
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(
        default=False,
        help_text="Inactive until an admin activates the agency.",
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Set when an admin approves this agency.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Agency'
        verbose_name_plural = 'Agencies'

    def __str__(self):
        return self.name

    def has_member(self, user):
        return self.users.filter(id=user.id, is_active=True).exists()



class User(AbstractUser):
    """
    Custom user model with email-based authentication
    """
    username = None  # Remove username field
    email = models.EmailField(
        unique=True,
        error_messages={
            'unique': "A user with that email already exists.",
        }
    )
    role = models.ForeignKey(
        Role, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='users'
    )
    agency = models.ForeignKey(
                Agency,
                on_delete=models.SET_NULL,
                null=True,
                blank=True,
                related_name='users',
                help_text="Agency this user belongs to (for agency members only)"
            )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email is already required as USERNAME_FIELD

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    def has_role(self, role_name):
        """
        Check if user has a specific role (dynamic check)
        Args:
            role_name: Role name string (case-insensitive)
        Returns:
            Boolean indicating if user has the role
        """
        return self.role and self.role.name.lower() == role_name.lower()

    def get_role_name(self):
        """Get the user's role name"""
        return self.role.name if self.role else None

    def has_perm_codename(self, perm_codename):
        """
        Check if user has a specific permission through their role
        Args:
            perm_codename: Permission codename string (e.g., 'roles.view')
        Returns:
            Boolean indicating if user has the permission
        """
        if self.is_superuser:
            return True
        if not self.role or not self.role.is_active:
            return False
        return self.role.permissions.filter(codename=perm_codename).exists()


    def has_dashboard_access(self, dashboard_code):
        """
        Check if user has access to a dashboard via their role
        """
        if self.is_superuser:
            return True
        if not self.role or not self.role.is_active:
            return False
        return self.role.dashboards.filter(code=dashboard_code, is_active=True).exists()


    def get_all_permissions(self):
        """Get all permission codenames for this user"""
        if not self.role:
            return []
        return self.role.get_permission_codenames()


    def is_agency_member(self):
        return self.agency is not None and self.has_role('agency')

    def get_agency_sessions(self):
        if not self.agency:
            return []
        from user_sessions.models import Session
        return Session.objects.filter(agency=self.agency)

    def has_active_subscription(self):
        if self.is_superuser or self.has_role('admin'):
            return True
        now = timezone.now()
        return self.subscriptions.filter(
            status__in=[UserSubscription.STATUS_ACTIVE, UserSubscription.STATUS_TRIALING],
        ).filter(
            models.Q(current_period_end__isnull=True) | models.Q(current_period_end__gt=now)
        ).exists()


class SubscriptionPlan(models.Model):
    INTERVAL_ONE_TIME = 'one_time'
    INTERVAL_MONTH = 'month'
    INTERVAL_YEAR = 'year'

    BILLING_INTERVAL_CHOICES = [
        (INTERVAL_ONE_TIME, 'One time'),
        (INTERVAL_MONTH, 'Monthly'),
        (INTERVAL_YEAR, 'Yearly'),
    ]

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='usd')
    billing_interval = models.CharField(
        max_length=20,
        choices=BILLING_INTERVAL_CHOICES,
        default=INTERVAL_MONTH,
    )
    stripe_product_id = models.CharField(max_length=255, blank=True)
    stripe_price_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='Optional. If empty, checkout uses the price configured here.',
    )
    question_gate_after = models.PositiveIntegerField(
        default=8,
        help_text='Users must subscribe after this many answered journey questions.',
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'id']
        verbose_name = 'Subscription plan'
        verbose_name_plural = 'Subscription plans'

    def __str__(self):
        return f"{self.name} - {self.currency.upper()} {self.price}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            SubscriptionPlan.objects.exclude(pk=self.pk).filter(is_active=True).update(is_active=False)

    @classmethod
    def active_plan(cls):
        return cls.objects.filter(is_active=True).order_by('display_order', 'id').first()


class UserSubscription(models.Model):
    STATUS_INCOMPLETE = 'incomplete'
    STATUS_ACTIVE = 'active'
    STATUS_TRIALING = 'trialing'
    STATUS_PAST_DUE = 'past_due'
    STATUS_CANCELED = 'canceled'
    STATUS_UNPAID = 'unpaid'

    STATUS_CHOICES = [
        (STATUS_INCOMPLETE, 'Incomplete'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_TRIALING, 'Trialing'),
        (STATUS_PAST_DUE, 'Past due'),
        (STATUS_CANCELED, 'Canceled'),
        (STATUS_UNPAID, 'Unpaid'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='subscriptions',
        on_delete=models.CASCADE,
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        related_name='user_subscriptions',
        on_delete=models.PROTECT,
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_INCOMPLETE)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, db_index=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, db_index=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'User subscription'
        verbose_name_plural = 'User subscriptions'

    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"

    @property
    def is_active(self):
        if self.status not in {self.STATUS_ACTIVE, self.STATUS_TRIALING}:
            return False
        return self.current_period_end is None or self.current_period_end > timezone.now()
