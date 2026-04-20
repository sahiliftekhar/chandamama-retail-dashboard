from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0019_sale_pricing_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='remarks',
            field=models.CharField(
                max_length=100,
                blank=True,
                null=True,
                help_text='Optional identification e.g. Bhagwa, Red Pattern (shown as PRODUCT - Remarks)'
            ),
        ),
    ]