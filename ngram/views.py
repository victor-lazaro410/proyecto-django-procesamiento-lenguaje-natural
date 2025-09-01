import json
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .services import default_simple_tokenize, ngram_frequencies

def _maybe_use_project_tokenizer(text: str):
    """
    Intenta usar una función de tokenización del proyecto si está disponible.
    Busca nombres comunes y, si falla, usa el fallback simple.
    """
    candidates = [
        # rutas potenciales (ajustables según el proyecto)
        "nlp.tokenize",
        "nlp.preprocessing.tokenize",
        "preprocess.tokenize",
        "text.preprocessing.tokenize",
        "utils.tokenize",
        "core.tokenize",
    ]
    for dotted in candidates:
        try:
            module_name, func_name = dotted.rsplit(".", 1)
            mod = __import__(module_name, fromlist=[func_name])
            func = getattr(mod, func_name, None)
            if callable(func):
                return func(text)
        except Exception:
            continue
    return default_simple_tokenize(text)

@require_http_methods(["GET", "POST"])
def ngrams_view(request: HttpRequest) -> HttpResponse:
    """
    Vista HTML con formulario simple y tabla de frecuencias.
    GET: muestra formulario. Si hay parámetros ?n=2&text=..., calcula y renderiza tabla.
    POST: idem con cuerpo del formulario.
    """
    if request.method == "GET":
        n = request.GET.get("n")
        text = request.GET.get("text", "")
    else:
        n = request.POST.get("n")
        text = request.POST.get("text", "")

    context = {"frequencies": None, "n": n, "text": text, "error": None}
    if n:
        try:
            n_val = int(n)
            if n_val < 2:
                raise ValueError("n debe ser >= 2")
            tokens = _maybe_use_project_tokenizer(text)
            freqs = ngram_frequencies(tokens, n_val)
            # Orden descendente por frecuencia
            sorted_items = sorted(freqs.items(), key=lambda kv: (-kv[1], kv[0]))
            context["frequencies"] = sorted_items
        except Exception as ex:
            context["error"] = str(ex)

    return render(request, "ngram/ngrams.html", context)

@require_http_methods(["POST"])
def ngrams_api(request: HttpRequest) -> JsonResponse:
    """
    Endpoint JSON. Cuerpo esperado (application/json):
    {
        "tokens": ["hola","mundo",...],  # opcional si se envía "text"
        "text": "texto libre",           # opcional si se envían tokens
        "n": 2
    }
    Devuelve: {"n": 2, "frequencies": [["hola mundo", 3], ...]}
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    n = payload.get("n")
    tokens = payload.get("tokens")
    text = payload.get("text", "")

    if not n or not isinstance(n, int):
        return JsonResponse({"error": "Debes enviar un entero 'n' >= 2"}, status=400)
    if n < 2:
        return JsonResponse({"error": "n debe ser >= 2"}, status=400)

    if not tokens and text:
        tokens = _maybe_use_project_tokenizer(text)
    if not tokens:
        return JsonResponse({"error": "Debes enviar 'tokens' o 'text'."}, status=400)

    try:
        freqs = ngram_frequencies(tokens, n)
        sorted_items = sorted(freqs.items(), key=lambda kv: (-kv[1], kv[0]))
        return JsonResponse({"n": n, "frequencies": sorted_items})
    except Exception as ex:
        return JsonResponse({"error": str(ex)}, status=500)