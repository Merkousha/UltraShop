from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from core.models import Store


@receiver(pre_save, sender=Store)
def capture_store_username(sender, instance: Store, **kwargs):
    if not instance.pk:
        instance._old_username = None
        return

    instance._old_username = (
        sender.objects.filter(pk=instance.pk).values_list("username", flat=True).first()
    )


@receiver(post_save, sender=Store)
def provision_or_sync_store_schema(sender, instance: Store, created: bool, **kwargs):
    from core.provisioning import provision_store_schema, sync_store_tenant_slug

    if created:
        provision_store_schema(instance)
        return

    old_username = getattr(instance, "_old_username", None)
    if old_username and old_username != instance.username:
        sync_store_tenant_slug(instance, old_username)