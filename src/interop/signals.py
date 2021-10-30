from django.db.models.signals import post_save

from interop.odlc import post_odlc

post_save.connect(post_odlc, sender=imp_module.models.ImpODLC)