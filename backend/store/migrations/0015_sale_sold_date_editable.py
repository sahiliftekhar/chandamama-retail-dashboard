from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0014_remove_stock_unique_constraint'),
    ]

    operations = [
        # ✅ Fix 1: Make sold_date editable (remove auto_now_add)
        migrations.AlterField(
            model_name='sale',
            name='sold_date',
            field=models.DateTimeField(
                blank=True,
                null=True,
                default=None,
                help_text='Leave blank to use current date/time',
            ),
        ),
    ]