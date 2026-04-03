# ============================================================
#  store/audit_mixin.py
#  Add this mixin to any ModelAdmin to auto-log all changes
# ============================================================

from .models import AuditLog


def get_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def get_changes(old_obj, new_obj):
    """Compare two objects and return a string of changes."""
    if old_obj is None:
        return ""
    changes = []
    for field in new_obj._meta.fields:
        fname = field.name
        try:
            old_val = getattr(old_obj, fname)
            new_val = getattr(new_obj, fname)
            if str(old_val) != str(new_val):
                changes.append(f"{fname}: '{old_val}' → '{new_val}'")
        except Exception:
            pass
    return " | ".join(changes)


class AuditLogMixin:
    """
    Mixin for ModelAdmin classes.
    Automatically logs CREATE, UPDATE, DELETE actions.
    """

    def save_model(self, request, obj, form, change):
        # Fetch old object before saving
        old_obj = None
        if change and obj.pk:
            try:
                old_obj = obj.__class__.objects.get(pk=obj.pk)
            except Exception:
                pass

        super().save_model(request, obj, form, change)

        action  = 'UPDATE' if change else 'CREATE'
        changes = get_changes(old_obj, obj) if change else ""

        AuditLog.objects.create(
            user        = request.user,
            action      = action,
            model_name  = obj.__class__.__name__,
            object_id   = str(obj.pk),
            object_repr = str(obj)[:300],
            changes     = changes[:1000] if changes else "",
            ip_address  = get_ip(request),
        )

    def delete_model(self, request, obj):
        AuditLog.objects.create(
            user        = request.user,
            action      = 'DELETE',
            model_name  = obj.__class__.__name__,
            object_id   = str(obj.pk),
            object_repr = str(obj)[:300],
            changes     = "",
            ip_address  = get_ip(request),
        )
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            AuditLog.objects.create(
                user        = request.user,
                action      = 'DELETE',
                model_name  = obj.__class__.__name__,
                object_id   = str(obj.pk),
                object_repr = str(obj)[:300],
                changes     = "",
                ip_address  = get_ip(request),
            )
        super().delete_queryset(request, queryset)