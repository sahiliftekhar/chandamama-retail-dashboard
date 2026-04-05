from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0010_alter_category_options_alter_category_id_and_more'),
    ]

    operations = [
        # ── Step 1: Add size field to Pricing ─────────────────────
        migrations.AddField(
            model_name='pricing',
            name='size',
            field=models.CharField(max_length=10, default='FREE'),
            preserve_default=False,
        ),

        # ── Step 2: Remove selling_price from Pricing ─────────────
        migrations.RemoveField(
            model_name='pricing',
            name='selling_price',
        ),

        # ── Step 3: Change Pricing.product to ForeignKey ──────────
        migrations.AlterField(
            model_name='pricing',
            name='product',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='pricings',
                to='store.product',
            ),
        ),

        # ── Step 4: Add unique_together for product+size ──────────
        migrations.AlterUniqueTogether(
            name='pricing',
            unique_together={('product', 'size')},
        ),

        # ── Step 5: Change low_stock_threshold default to 2 ───────
        migrations.AlterField(
            model_name='product',
            name='low_stock_threshold',
            field=models.PositiveIntegerField(default=2),
        ),

        # ── Step 6: Add unique_together for product name+category ─
        migrations.AlterUniqueTogether(
            name='product',
            unique_together={('name', 'category')},
        ),
    ]