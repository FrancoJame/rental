from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.db.utils import ProgrammingError, OperationalError

class ListingsConfig(AppConfig):
    name = 'listings'

    def ready(self):
        from django.contrib.auth import get_user_model

        def create_default_general_manager(sender, **kwargs):
            User = get_user_model()
            try:
                # The try block catches the error if the table listings_user is missing
                if not User.objects.filter(username='landlord').exists():
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
            except (ProgrammingError, OperationalError):
                # If the table doesn't exist yet, pass silently so migrations can finish
                pass

        post_migrate.connect(create_default_general_manager, sender=self)