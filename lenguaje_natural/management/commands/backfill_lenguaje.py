from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
from lenguaje_natural.models import DocumentoLN
from lenguaje_natural.utils import clean_and_tokenize
import collections, json, os
from pathlib import Path

class Command(BaseCommand):
    help = "Importa archivos legacy (p.ej. media/uploads/last.txt) a DocumentoLN."

    def handle(self, *args, **options):
        media = settings.MEDIA_ROOT
        candidates = [
            Path(media) / "uploads_lenguaje" / "last.txt",
            Path(media) / "uploads" / "last.txt",
        ]
        imported = 0
        for path in candidates:
            if not path.exists():
                continue
            if DocumentoLN.objects.filter(nombre_original=path.name).exists():
                self.stdout.write(self.style.WARNING(f"Ya existe registro para {path.name}, omitiendo."))
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            tokens = clean_and_tokenize(text)
            top = collections.Counter(tokens).most_common(30)
            doc = DocumentoLN(nombre_original=path.name); doc.save()
            doc.archivo.save(path.name, ContentFile(text.encode("utf-8")), save=False)
            doc.tokens_preview = ", ".join(tokens[:50])
            doc.top_json = json.dumps(top, ensure_ascii=False)
            doc.save()
            imported += 1
            self.stdout.write(self.style.SUCCESS(f"Importado: {path}"))
        self.stdout.write(self.style.SUCCESS(f"Listo. Importados: {imported}"))
