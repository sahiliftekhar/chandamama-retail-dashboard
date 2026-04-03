from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_superuser(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    if not User.objects.filter(username='admin').exists():
        User.objects.create(
            username='admin',
            password=make_password('pass@123'),
            is_superuser=True,
            is_staff=True,
            is_active=True,
            email='admin@myeod.com',
            first_name='CHANDA',
            last_name='MAMA',
        )


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0008_alter_category_id_alter_pricing_id_alter_product_id_and_more'),
    ]

    operations = [
        migrations.RunPython(create_superuser, migrations.RunPython.noop),
    ]