import os, json, collections
from django.conf import settings
from django import forms
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.core.files.base import ContentFile
from .utils import clean_and_tokenize
from .models import DocumentoLN
class UploadForm(forms.Form):
    file = forms.FileField(label="Archivo (.txt o .csv)")
UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, "uploads_lenguaje")
LAST_UPLOAD_PATH = os.path.join(UPLOAD_DIR, "last.txt")
LEGACY_UPLOAD_PATHS = [
    LAST_UPLOAD_PATH,
    os.path.join(settings.MEDIA_ROOT, "uploads", "last.txt"),
]
def _ensure_doc_from_last_upload():
    if DocumentoLN.objects.exists():
        return
    path = next((p for p in LEGACY_UPLOAD_PATHS if os.path.exists(p)), None)
    if not path: return
    text = open(path, "r", encoding="utf-8", errors="ignore").read()
    tokens = clean_and_tokenize(text)
    top = collections.Counter(tokens).most_common(30)
    name = os.path.basename(path)
    if DocumentoLN.objects.filter(nombre_original=name).exists(): return
    doc = DocumentoLN(nombre_original=name); doc.save()
    doc.archivo.save(name, ContentFile(text.encode("utf-8")), save=False)
    doc.tokens_preview = ", ".join(tokens[:50])
    doc.top_json = json.dumps(top, ensure_ascii=False)
    doc.save()
def _tabla_top():
    doc = DocumentoLN.objects.order_by("-created_at").first()
    if doc and (doc.top_json or "").strip():
        try: return json.loads(doc.top_json)
        except Exception: pass
    for p in LEGACY_UPLOAD_PATHS:
        if os.path.exists(p):
            text = open(p, "r", encoding="utf-8", errors="ignore").read()
            tokens = clean_and_tokenize(text)
            return collections.Counter(tokens).most_common(30)
    return None
def _tokens_preview(limit=50):
    doc = DocumentoLN.objects.order_by("-created_at").first()
    if doc and (doc.tokens_preview or "").strip():
        return [t.strip() for t in doc.tokens_preview.split(",") if t.strip()][:limit]
    for p in LEGACY_UPLOAD_PATHS:
        if os.path.exists(p):
            text = open(p, "r", encoding="utf-8", errors="ignore").read()
            tokens = clean_and_tokenize(text)
            return tokens[:limit]
    return None
def index(request):
    _ensure_doc_from_last_upload()
    tabla = _tabla_top()
    return render(request, "lenguaje_natural/index.html", {"tabla": tabla, "tokens": _tokens_preview()})
@csrf_protect
def upload(request):
    if request.method != "POST" or "file" not in request.FILES:
        return render(request, "lenguaje_natural/index.html", {"tabla": _tabla_top(), "msg": None, "tokens": _tokens_preview()}, status=400)
    f = request.FILES["file"]
    fname = f.name.lower()
    if not (fname.endswith(".txt") or fname.endswith(".csv")):
        return render(request, "lenguaje_natural/index.html", {"tabla": _tabla_top(), "msg": "Solo .txt o .csv", "tokens": _tokens_preview()}, status=400)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(LAST_UPLOAD_PATH, "wb") as dest:
        for chunk in f.chunks():
            dest.write(chunk)
    text = open(LAST_UPLOAD_PATH, "r", encoding="utf-8", errors="ignore").read()
    tokens = clean_and_tokenize(text)
    top = collections.Counter(tokens).most_common(30)
    doc = DocumentoLN(nombre_original=f.name); doc.save()
    doc.archivo.save(f.name, ContentFile(open(LAST_UPLOAD_PATH, "rb").read()), save=False)
    doc.tokens_preview = ", ".join(tokens[:50])
    doc.top_json = json.dumps(top, ensure_ascii=False)
    doc.save()
    return render(request, "lenguaje_natural/index.html", {"tabla": top, "msg": "Archivo subido y guardado en BD.", "tokens": tokens[:50]})
def histograma(request):
    _ensure_doc_from_last_upload()
    tabla = _tabla_top()
    if tabla is None:
        return render(request, "lenguaje_natural/index.html", {"tabla": None, "msg": "Aún no hay archivo. Sube uno primero.", "tokens": None}, status=400)
    return render(request, "lenguaje_natural/index.html", {"tabla": tabla, "tokens": _tokens_preview()})
