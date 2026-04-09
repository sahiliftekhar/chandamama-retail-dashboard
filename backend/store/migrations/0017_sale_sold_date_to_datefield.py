from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0016_alter_stock_unique_together'),
    ]

    operations = [
        # ✅ Only change sold_date to DateField — no stock constraint
        migrations.AlterField(
            model_name='sale',
            name='sold_date',
            field=models.DateField(
                blank=True,
                null=True,
                default=None,
                help_text="Leave blank to use today's date",
            ),
        ),
    ]
