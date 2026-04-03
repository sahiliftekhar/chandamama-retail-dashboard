import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Ensures a superuser exists — runs on every container start'

    def handle(self, *args, **kwargs):
        username   = 'admin'
        password = os.environ.get('DJANGO_ADMIN_PASSWORD', 'pass@123')
        email      = 'admin@myeod.com'
        first_name = 'Chanda'
        last_name  = 'Mama'

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            self.stdout.write(self.style.SUCCESS(
                f'✅ Superuser created: {username} / {password}'
            ))
        else:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.first_name  = first_name
            user.last_name   = last_name
            user.is_superuser = True
            user.is_staff     = True
            user.is_active    = True
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f'✅ Superuser verified: {username} / {password}'
            ))