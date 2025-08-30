from django.db import models
from django.utils import timezone
def pat_upload_path(instance, filename):
    dt = getattr(instance, 'created_at', None) or timezone.now()
    return f"patrones/{dt:%Y/%m/%d}/orig/{filename}"
def pat_output_path(instance, filename):
    dt = getattr(instance, 'created_at', None) or timezone.now()
    return f"patrones/{dt:%Y/%m/%d}/out/{filename}"
class DocumentoPatrones(models.Model):
    archivo = models.FileField(upload_to=pat_upload_path)
    nombre_original = models.CharField(max_length=255, blank=True)
    archivo_transformado = models.FileField(upload_to=pat_output_path, blank=True, null=True)
    reservadas = models.IntegerField(default=0)
    variables = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.nombre_original or self.archivo.name} ({self.created_at:%Y-%m-%d %H:%M})"
