from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from myapp.models import Employee, Serveur, EtatSysteme
from myapp.sync import sync_data_from_csv, disable_signals

@receiver(post_save, sender=Employee)
@receiver(post_save, sender=Serveur)
@receiver(post_save, sender=EtatSysteme)
def post_save_handler(sender, instance, **kwargs):
    if not disable_signals:
        sync_data_from_csv()

@receiver(post_delete, sender=Employee)
@receiver(post_delete, sender=Serveur)
@receiver(post_delete, sender=EtatSysteme)
def post_delete_handler(sender, instance, **kwargs):
    if not disable_signals:
        sync_data_from_csv()
