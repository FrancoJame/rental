from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create default general manager account if it does not exist'

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.filter(username='landlord').exists():
            self.stdout.write(self.style.SUCCESS('Manager account already exists'))
            return

        user = User.objects.create_user(
            username='landlord',
            email='landlord@example.com',
            password='landlord256',
            first_name='General',
            last_name='Manager',
            role=User.MANAGER,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save()
        
        self.stdout.write(self.style.SUCCESS('Manager account created successfully'))
