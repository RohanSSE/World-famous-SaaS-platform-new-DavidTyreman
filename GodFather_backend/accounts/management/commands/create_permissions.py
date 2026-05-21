"""
Management command to create initial permissions, roles, and dashboards
Usage: python manage.py create_permissions
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Permission, Role, Dashboard

User = get_user_model()

class Command(BaseCommand):
    help = 'Create initial permissions, roles, and dashboards for the application'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Creating dashboards...'))
        
        # Define dashboards
        dashboards_data = [
            {'code': 'tasks', 'name': 'Tasks', 'description': 'Task dashboard'},
            {'code': 'reviews', 'name': 'Reviews', 'description': 'Review dashboard'},
        ]
        
        created_dashboards = {}
        for dash_data in dashboards_data:
            dashboard, created = Dashboard.objects.get_or_create(
                code=dash_data['code'],
                defaults={
                    'name': dash_data['name'],
                    'description': dash_data.get('description', ''),
                }
            )
            created_dashboards[dash_data['code']] = dashboard
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created dashboard: {dashboard.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  - Dashboard already exists: {dashboard.name}'))

        self.stdout.write(self.style.SUCCESS('Creating permissions...'))
        
        # Define all permissions
        permissions_data = [
            {'codename': 'sessions.view', 'name': 'View Sessions', 'description': 'Can view all sessions'},
            {'codename': 'sessions.create', 'name': 'Create Sessions', 'description': 'Can create new sessions'},
            {'codename': 'sessions.update', 'name': 'Update Sessions', 'description': 'Can update session details'},
            {'codename': 'sessions.delete', 'name': 'Delete Sessions', 'description': 'Can delete sessions'},
            
            {'codename': 'answers.view', 'name': 'View Answers', 'description': 'Can view answers'},
            {'codename': 'answers.create', 'name': 'Create Answers', 'description': 'Can create/update answers'},
            {'codename': 'answers.update', 'name': 'Update Answers', 'description': 'Can update existing answers'},
            {'codename': 'answers.delete', 'name': 'Delete Answers', 'description': 'Can delete answers'},
            {'codename': 'answers.ai_suggest', 'name': 'Get AI Suggestions', 'description': 'Can request AI suggestions for answers'},
            
            {'codename': 'questions.view', 'name': 'View Questions', 'description': 'Can view all questions'},
            {'codename': 'questions.create', 'name': 'Create Questions', 'description': 'Can create new questions'},
            {'codename': 'questions.update', 'name': 'Update Questions', 'description': 'Can update questions'},
            {'codename': 'questions.delete', 'name': 'Delete Questions', 'description': 'Can delete questions'},
            
            {'codename': 'ai.view', 'name': 'View AI Output', 'description': 'Can view AI generated output'},
            {'codename': 'ai.generate', 'name': 'Generate AI Output', 'description': 'Can generate AI manifesto'},

            {'codename': 'agencies.view', 'name': 'View Agencies', 'description': 'Can view all agencies'},
            {'codename': 'agencies.create', 'name': 'Create Agency', 'description': 'Can create new agencies'},
            {'codename': 'agencies.update', 'name': 'Update Agency', 'description': 'Can update existing agencies'},
            {'codename': 'agencies.delete', 'name': 'Delete Agency', 'description': 'Can delete agencies'},
            
            {'codename': 'roles.view', 'name': 'View Roles', 'description': 'Can view all roles'},
            {'codename': 'roles.create', 'name': 'Create Role', 'description': 'Can create new roles'},
            {'codename': 'roles.update', 'name': 'Update Role', 'description': 'Can update existing roles'},
            {'codename': 'roles.delete', 'name': 'Delete Role', 'description': 'Can delete roles'},
            
            {'codename': 'permissions.view', 'name': 'View Permissions', 'description': 'Can view all permissions'},
            {'codename': 'permissions.create', 'name': 'Create Permission', 'description': 'Can create new permissions'},
            {'codename': 'permissions.update', 'name': 'Update Permission', 'description': 'Can update existing permissions'},
            {'codename': 'permissions.delete', 'name': 'Delete Permission', 'description': 'Can delete permissions'},
            
            {'codename': 'users.view', 'name': 'View Users', 'description': 'Can view all users'},
            {'codename': 'users.create', 'name': 'Create User', 'description': 'Can create new users'},
            {'codename': 'users.update', 'name': 'Update User', 'description': 'Can update existing users'},
            {'codename': 'users.delete', 'name': 'Delete User', 'description': 'Can delete users'},

            {'codename': 'comments.view', 'name': 'View Comments', 'description': 'Can view all comments'},
            {'codename': 'comments.create', 'name': 'Create Comments', 'description': 'Can create new comments'},
            {'codename': 'comments.update', 'name': 'Update Comments', 'description': 'Can update existing comments'},
            {'codename': 'comments.delete', 'name': 'Delete Comments', 'description': 'Can delete comments'},
        ]
        
        created_permissions = {}
        for perm_data in permissions_data:
            permission, created = Permission.objects.get_or_create(
                codename=perm_data['codename'],
                defaults={
                    'name': perm_data['name'],
                    'description': perm_data.get('description', '')
                }
            )
            created_permissions[perm_data['codename']] = permission
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created permission: {perm_data["name"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'  - Permission already exists: {perm_data["name"]}'))

        self.stdout.write(self.style.SUCCESS('Creating roles and assigning permissions & dashboards...'))
        
        # Define roles with permissions and dashboards
        roles_data = [
            {
                'name': 'admin',
                'description': 'Administrator with full access',
                'permissions': [
                    'roles.view', 'roles.create', 'roles.update', 'roles.delete',
                    'permissions.view', 'permissions.create', 'permissions.update', 'permissions.delete',
                    'users.view', 'users.create', 'users.update', 'users.delete',
                ],
                'dashboards': ['tasks', 'reviews']  # admin sees all dashboards
            },
            {
                'name': 'client',
                'description': 'Client role with task access',
                'permissions': [
                    'users.view', 'users.update',
                    'sessions.view', 'sessions.create', 'sessions.update',
                    'agencies.view',
                    'answers.view', 'answers.create', 'answers.update', 'answers.delete', 'answers.ai_suggest',
                ],
                'dashboards': ['tasks']
            },
            {
                'name': 'agency',
                'description': 'Agency role with review dashboard access',
                'permissions': [
                    'users.view'
                ],
                'dashboards': ['reviews']  # reviewer sees only reviews
            },
        ]
        
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={'description': role_data['description'], 'is_active': True}
            )
            
            # Assign permissions
            perms_to_add = [created_permissions[p] for p in role_data.get('permissions', []) if p in created_permissions]
            role.permissions.set(perms_to_add)
            
            # Assign dashboards
            dashboards_to_add = [created_dashboards[d] for d in role_data.get('dashboards', []) if d in created_dashboards]
            role.dashboards.set(dashboards_to_add)
            
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ Created role: {role.name} with {len(perms_to_add)} permissions and {len(dashboards_to_add)} dashboards'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'  - Role already exists: {role.name} (updated permissions & dashboards)'
                ))

        self.stdout.write(self.style.SUCCESS('✅ Permissions, dashboards, and roles setup completed!'))

        # Optionally, check for admin user
        admin_email = 'admin@example.com'
        if not User.objects.filter(email=admin_email).exists():
            self.stdout.write(self.style.WARNING(f'No admin user found. Create one with: python manage.py createsuperuser'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Admin user exists: {admin_email}'))
