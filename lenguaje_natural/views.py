import os, json, collections
from django.conf import settings
from django import forms
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.core.files.base import ContentFile
from .utils import clean_and_tokenize
from .models import DocumentoLN
from ngram.services import ngram_frequencies

class UploadForm(forms.Form):
    file = forms.FileField(label="Archivo (.txt o .csv)")

UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, "uploads_lenguaje")
LAST_UPLOAD_PATH = os.path.join(UPLOAD_DIR, "last.txt")

def _compute_all(text):
    tokens = clean_and_tokenize(text)
    top_unigrams = collections.Counter(tokens).most_common(30)
    bigrams = ngram_frequencies(tokens, 2)
    trigrams = ngram_frequencies(tokens, 3)
    bigram_tabla = sorted(bigrams.items(), key=lambda kv: (-kv[1], kv[0]))[:50]
    trigram_tabla = sorted(trigrams.items(), key=lambda kv: (-kv[1], kv[0]))[:50]
    return tokens, top_unigrams, bigram_tabla, trigram_tabla

def _render_index(request, msg=None, tokens=None, tabla=None, bigram_tabla=None, trigram_tabla=None, status_code=200):
    ctx = {
        "form": UploadForm(),
        "msg": msg,
        "tokens": tokens,
        "tabla": tabla,
        "bigram_tabla": bigram_tabla,
        "trigram_tabla": trigram_tabla,
    }
    return render(request, "lenguaje_natural/index.html", ctx, status=status_code)

def index(request):
    # Si existe un último upload, muestra sus datos (sin error)
    if os.path.exists(LAST_UPLOAD_PATH):
        text = open(LAST_UPLOAD_PATH, "r", encoding="utf-8", errors="ignore").read()
        tokens, tabla, bigram_tabla, trigram_tabla = _compute_all(text)
        return _render_index(request, None, tokens[:50], tabla, bigram_tabla, trigram_tabla)
    return _render_index(request, None, None, None, None, None)

@csrf_protect
def upload(request):
    if request.method != "POST" or "file" not in request.FILES:
        # Petición inválida: mostrar página con lo último disponible si existe
        if os.path.exists(LAST_UPLOAD_PATH):
            text = open(LAST_UPLOAD_PATH, "r", encoding="utf-8", errors="ignore").read()
            tokens, tabla, bigram_tabla, trigram_tabla = _compute_all(text)
            return _render_index(request, None, tokens[:50], tabla, bigram_tabla, trigram_tabla, status_code=400)
        return _render_index(request, "Sube un archivo .txt o .csv", None, None, None, None, status_code=400)

    f = request.FILES["file"]
    fname = f.name.lower()
    if not (fname.endswith(".txt") or fname.endswith(".csv")):
        return _render_index(request, "Solo se permiten archivos .txt o .csv", None, None, None, None, status_code=400)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(LAST_UPLOAD_PATH, "wb") as dest:
        for chunk in f.chunks():
            dest.write(chunk)

    text = open(LAST_UPLOAD_PATH, "r", encoding="utf-8", errors="ignore").read()
    tokens, tabla, bigram_tabla, trigram_tabla = _compute_all(text)

    # Guardar en BD (como hacía el flujo original)
    top = tabla
    doc = DocumentoLN(nombre_original=f.name)
    doc.save()
    with open(LAST_UPLOAD_PATH, "rb") as rb:
        doc.archivo.save(f.name, ContentFile(rb.read()), save=False)
    doc.tokens_preview = ", ".join(tokens[:50])
    doc.top_json = json.dumps(top, ensure_ascii=False)
    doc.save()

    return _render_index(request, "Archivo subido y procesado.", tokens[:50], tabla, bigram_tabla, trigram_tabla)

def histograma(request):
    if not os.path.exists(LAST_UPLOAD_PATH):
        return _render_index(request, "No hay archivo. Sube uno primero.", None, None, None, None, status_code=400)
    text = open(LAST_UPLOAD_PATH, "r", encoding="utf-8", errors="ignore").read()
    tokens, tabla, bigram_tabla, trigram_tabla = _compute_all(text)
    return _render_index(request, None, tokens[:50], tabla, bigram_tabla, trigram_tabla)