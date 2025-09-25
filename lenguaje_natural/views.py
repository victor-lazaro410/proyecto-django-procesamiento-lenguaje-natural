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


# --- Parámetros por defecto para n-gramas en esta sección ---
N_DEFAULT = 2  # bigramas por defecto

def _get_n_from_request(request):
    """Obtiene 'n' de request (GET o POST). Si no está o es inválido, usa N_DEFAULT."""
    val = None
    try:
        if hasattr(request, "POST") and request.POST.get("n"):
            val = int(request.POST.get("n"))
        elif hasattr(request, "GET") and request.GET.get("n"):
            val = int(request.GET.get("n"))
    except Exception:
        val = None
    if val is None or val < 2:
            val = N_DEFAULT
    return val


def _parse_n(request, default_n=2):
    try:
        n_str = request.GET.get("n") or request.POST.get("n")
        if n_str is None or str(n_str).strip() == "":
            return int(default_n)
        n = int(n_str)
    except Exception:
        n = int(default_n)
    return max(1, min(n, 10))

def _ngram_table(tokens, n):
    if n == 1:
        import collections
        return sorted(collections.Counter(tokens).items(), key=lambda kv: (-kv[1], kv[0]))[:50]
    from ngram.services import ngram_frequencies
    freqs = ngram_frequencies(tokens, n)
    return sorted(freqs.items(), key=lambda kv: (-kv[1], kv[0]))[:50]



def _compute_all(text, n=None):
    tokens = clean_and_tokenize(text)
    top_unigrams = collections.Counter(tokens).most_common(30)
    # tablas fijas
    bigram_tabla = _ngram_table(tokens, 2)
    trigram_tabla = _ngram_table(tokens, 3)
    # tabla configurable
    ngram_tabla = _ngram_table(tokens, n) if n else None
    return tokens, top_unigrams, bigram_tabla, trigram_tabla, ngram_tabla




def _render_index(request, msg=None, tokens=None, tabla=None, bigram_tabla=None, trigram_tabla=None, ngram_tabla=None, ngram_n=None, status_code=200):
    ctx = {
        "form": UploadForm(),
        "msg": msg,
        "tokens": tokens,
        "tabla": tabla,
        "bigram_tabla": bigram_tabla,
        "trigram_tabla": trigram_tabla,
        "ngram_tabla": ngram_tabla,
        "ngram_n": ngram_n,
    }
    return render(request, "lenguaje_natural/index.html", ctx, status=status_code)




def index(request):
    """Pantalla inicial limpia: no pre-carga ningún TXT ni n-gramas.
    El usuario debe subir un archivo desde el formulario.
    """
    return _render_index(request, None, None, None, None, None)


@csrf_protect
def upload(request):
    if request.method != "POST" or "file" not in request.FILES:
        return _render_index(request, "Sube un archivo .txt o .csv", None, None, None, None, status_code=400)

    f = request.FILES["file"]
    fname = f.name.lower()
    if not (fname.endswith(".txt") or fname.endswith(".csv")):
        return _render_index(request, "Solo se permiten .txt o .csv", None, None, None, None, status_code=400)

    # Guardar archivo en carpeta uploads
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    save_path = os.path.join(UPLOAD_DIR, f.name)
    with open(save_path, "wb") as dest:
        for chunk in f.chunks():
            dest.write(chunk)

    # Guardar como "último" para otros módulos si hace falta
    with open(LAST_UPLOAD_PATH, "wb") as dest:
        for chunk in f.chunks():
            dest.write(chunk)

    return _render_index(request, "Archivo subido con éxito. Ahora puedes procesarlo en la sección que necesites.", None, None, None, None)
def histograma(request):
    if not os.path.exists(LAST_UPLOAD_PATH):
        return _render_index(request, "No hay archivo. Sube uno primero.", None, None, None, None, status_code=400)
    text = open(LAST_UPLOAD_PATH, "r", encoding="utf-8", errors="ignore").read()
    tokens, tabla, bigram_tabla, trigram_tabla, ngram_tabla = _compute_all(text, _get_n_from_request(request))
    return _render_index(request, None, tokens[:50], tabla, bigram_tabla, trigram_tabla, ngram_tabla, ngram_n=_get_n_from_request(request))


@csrf_protect
def calcular(request):
    """Calcula n-gramas (n>=2) bajo demanda usando el último archivo subido."""
    n = _get_n_from_request(request)
    if not os.path.exists(LAST_UPLOAD_PATH):
        return _render_index(request, "No hay archivo. Sube uno primero.", None, None, None, None, status_code=400)
    text = open(LAST_UPLOAD_PATH, "r", encoding="utf-8", errors="ignore").read()
    tokens = clean_and_tokenize(text)
    from ngram.services import ngram_frequencies as _freq
    unis = _freq(tokens, 1)[:30]  # Top 30 palabras (unigramas)
    ngram_tabla = _freq(tokens, n)
    bigram_tabla = []
    trigram_tabla = []
    msg = f"Cálculo realizado con n={n}."
    return _render_index(request, msg, tokens[:50], unis, bigram_tabla, trigram_tabla, ngram_tabla, ngram_n=n)
