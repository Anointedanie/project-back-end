"""
Django management command to create test users for development.
Usage: python manage.py create_test_users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates test users for development'
    
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Creating test users...'))
        
        # Create superuser (admin)
        if not User.objects.filter(email='admin@example.com').exists():
            User.objects.create_superuser(
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(self.style.SUCCESS('✓ Created superuser: admin@example.com (password: admin123)'))
        else:
            self.stdout.write(self.style.WARNING('✗ Superuser admin@example.com already exists'))
        
        # Create admin user (can manage products)
        if not User.objects.filter(email='productadmin@example.com').exists():
            User.objects.create_user(
                email='productadmin@example.com',
                password='admin123',
                first_name='Product',
                last_name='Admin',
                is_admin=True
            )
            self.stdout.write(self.style.SUCCESS('✓ Created admin user: productadmin@example.com (password: admin123)'))
        else:
            self.stdout.write(self.style.WARNING('✗ Admin user productadmin@example.com already exists'))
        
        # Create regular users (buyers)
        regular_users = [
            {
                'email': 'john.doe@example.com',
                'password': 'user123',
                'first_name': 'John',
                'last_name': 'Doe'
            },
            {
                'email': 'jane.smith@example.com',
                'password': 'user123',
                'first_name': 'Jane',
                'last_name': 'Smith'
            },
            {
                'email': 'bob.wilson@example.com',
                'password': 'user123',
                'first_name': 'Bob',
                'last_name': 'Wilson'
            }
        ]
        
        for user_data in regular_users:
            if not User.objects.filter(email=user_data['email']).exists():
                User.objects.create_user(**user_data)
                self.stdout.write(self.style.SUCCESS(f"✓ Created regular user: {user_data['email']} (password: user123)"))
            else:
                self.stdout.write(self.style.WARNING(f"✗ Regular user {user_data['email']} already exists"))
        
        self.stdout.write(self.style.SUCCESS('\n=== Test Users Created Successfully ==='))
        self.stdout.write(self.style.SUCCESS('\nYou can now use these credentials to test:'))
        self.stdout.write(self.style.SUCCESS('Superuser: admin@example.com / admin123'))
        self.stdout.write(self.style.SUCCESS('Product Admin: productadmin@example.com / admin123'))
        self.stdout.write(self.style.SUCCESS('Regular Users: john.doe@example.com, jane.smith@example.com, bob.wilson@example.com / user123'))
