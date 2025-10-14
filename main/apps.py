from django.apps import AppConfig
from django.contrib.auth.models import User
from django.db.utils import OperationalError


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        from .models import Profile
        try:
            if not User.objects.filter(username="admin").exists():
                user = User.objects.create_user(username="admin", password="admin123")
                Profile.objects.create(user=user, is_admin=True)
                print("Default admin user created.")
        except OperationalError:
            pass