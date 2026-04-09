from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0015_sale_sold_date_editable'),
    ]

    operations = [
        # Keep stock unique_together removed — no constraint needed
    ]