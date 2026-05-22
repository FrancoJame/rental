from django.apps import AppConfig
from django.db.models.signals import post_migrate


class ListingsConfig(AppConfig):
    name = 'listings'

    def ready(self):
        from django.contrib.auth import get_user_model

        def create_default_general_manager(sender, **kwargs):
            User = get_user_model()
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

        post_migrate.connect(create_default_general_manager, sender=self)
