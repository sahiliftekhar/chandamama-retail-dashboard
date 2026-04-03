from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date


# -----------------------------
# SECTION (Male, Female, Kids)
# -----------------------------
class Section(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# -----------------------------
# CATEGORY (Upperwear, Bottomwear)
# -----------------------------
class Category(models.Model):
    name = models.CharField(max_length=100)
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ('name', 'section')
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"{self.section.name} - {self.name}"


# -----------------------------
# PRODUCT
# -----------------------------
class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    buy_date = models.DateField(default=date.today)
    low_stock_threshold = models.PositiveIntegerField(default=3)  # Added low_stock_threshold field

    def __str__(self):
        return self.name


# -----------------------------
# PRICING (One-to-One with Product)
# -----------------------------
class Pricing(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    purchase_rate = models.DecimalField(max_digits=10, decimal_places=2)
    marked_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def clean(self):
        # Auto-calculate marked price if empty
        if not self.marked_price:
            self.marked_price = self.purchase_rate * Decimal("1.50")

        # Auto-fill selling price if empty
        if not self.selling_price:
            self.selling_price = self.marked_price

        # Validate minimum margin (20%)
        min_allowed = self.purchase_rate * Decimal("1.20")

        if self.selling_price < min_allowed:
            raise ValidationError(
                f"Selling price cannot be below 20% margin. Minimum allowed: {min_allowed}"
            )

    def margin_percent(self):
        return round(
            ((self.selling_price - self.purchase_rate) / self.purchase_rate) * 100,
            2
        )

    def __str__(self):
        return f"Pricing for {self.product.name}"



# -----------------------------
# STOCK (Size-based)
# -----------------------------
class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=10)
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ('product', 'size')

    def __str__(self):
        return f"{self.product.name} - {self.size}"


# -----------------------------
# SALES (Daily EOD Records)
# -----------------------------
class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=10)
    quantity = models.PositiveIntegerField()

    purchase_rate_snapshot = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    marked_price_snapshot = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    profit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    sold_date = models.DateTimeField(auto_now_add=True)

    def clean(self):

        # Fetch pricing first
        try:
            pricing = Pricing.objects.get(product=self.product)
        except Pricing.DoesNotExist:
            raise ValidationError("Pricing does not exist for this product.")

        purchase_rate = pricing.purchase_rate

        # Stock validation
        try:
            stock = Stock.objects.get(product=self.product, size=self.size)
        except Stock.DoesNotExist:
            raise ValidationError("Stock entry does not exist for this size.")

        if self.quantity > stock.quantity:
            raise ValidationError(
                f"Not enough stock. Available: {stock.quantity}"
            )

        # Margin validation
        min_allowed = purchase_rate * Decimal("1.20")
        if self.selling_price < min_allowed:
            raise ValidationError(
                f"Selling price cannot be below 20% margin. Minimum allowed: {min_allowed}"
            )

    def save(self, *args, **kwargs):

        pricing = Pricing.objects.get(product=self.product)

        # Snapshot pricing
        self.purchase_rate_snapshot = pricing.purchase_rate
        self.marked_price_snapshot = pricing.marked_price

        # Calculate profit
        self.profit = (
            (self.selling_price - self.purchase_rate_snapshot - self.discount)
            * self.quantity
        )

        super().save(*args, **kwargs)

        # Deduct stock
        stock = Stock.objects.get(product=self.product, size=self.size)
        stock.quantity -= self.quantity
        stock.save()

        # Low stock alert
        from .utils import send_whatsapp_alert

        if stock.quantity <= self.product.low_stock_threshold:
            message = f"""
⚠ LOW STOCK ALERT

Product: {self.product.name}
Size: {self.size}
Remaining Quantity: {stock.quantity}

Please restock soon.
            """
            send_whatsapp_alert(message)

    def __str__(self):
        return f"Sale - {self.product.name} ({self.size})"
    
class SystemSettings(models.Model):
    show_purchase_rate = models.BooleanField(default=True)

    class Meta:
        verbose_name        = "System Setting"
        verbose_name_plural = "System Settings"
        
    def __str__(self):
        return "System Settings"

# ── ADD THIS TO THE BOTTOM OF YOUR models.py ──────────────────────

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
    ]

    user        = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='audit_logs'
    )
    action      = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name  = models.CharField(max_length=100)
    object_id   = models.CharField(max_length=50, blank=True)
    object_repr = models.CharField(max_length=300)
    changes     = models.TextField(blank=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    timestamp   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name     = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        return f"{self.timestamp:%d %b %Y %H:%M} | {self.user} | {self.action} | {self.model_name}"