from django.db import models
from django.utils import timezone
def ln_upload_path(instance, filename):
    dt = getattr(instance, 'created_at', None) or timezone.now()
    return f"lenguaje/{dt:%Y/%m/%d}/{filename}"
class DocumentoLN(models.Model):
    archivo = models.FileField(upload_to=ln_upload_path)
    nombre_original = models.CharField(max_length=255, blank=True)
    tokens_preview = models.TextField(blank=True)
    top_json = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.nombre_original or self.archivo.name} ({self.created_at:%Y-%m-%d %H:%M})"
