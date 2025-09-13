import json
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .services import default_simple_tokenize, ngram_frequencies, mle_conditional_probabilities, format_prob_table, _split_sentences, add_sentence_boundaries

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

@require_http_methods(["GET", "POST"])
def ngrams_mle_view(request: HttpRequest) -> HttpResponse:
    """
    Página para calcular probabilidades condicionales (MLE) de n-gramas,
    con y sin fronteras de oración <s>, </s>.
    """
    ctx = {"result": None, "error": None}
    if request.method == "POST":
        text = request.POST.get("text", "")
        # Manejo de archivo subido (txt)
        uploaded_file = request.FILES.get("corpus_file")
        if uploaded_file and uploaded_file.name.endswith(".txt"):
            try:
                text = uploaded_file.read().decode("utf-8")
            except Exception:
                ctx["error"] = "No se pudo leer el archivo de texto. Asegúrate que sea UTF-8."
                return render(request, "ngram/ngrams_mle.html", ctx)

        n_str = request.POST.get("n", "2")
        try:
            n = int(n_str)
            if n < 2:
                raise ValueError("n debe ser >= 2")
        except Exception:
            ctx["error"] = "Debes indicar un entero n >= 2."
            return render(request, "ngram/ngrams_mle.html", ctx)

        # Tokenización
        tokens = _maybe_use_project_tokenizer(text)

        # Caso 1: sin fronteras
        try:
            probs_no_bound = mle_conditional_probabilities(tokens, n)
            table_no_bound = format_prob_table(probs_no_bound)
        except Exception as ex:
            ctx["error"] = f"Error (sin fronteras): {ex}"
            return render(request, "ngram/ngrams_mle.html", ctx)

        # Caso 2: con fronteras
        try:
            sent_tokens = _split_sentences(text)
            tokens_with_bounds = add_sentence_boundaries(sent_tokens)
            probs_with_bound = mle_conditional_probabilities(tokens_with_bounds, n)
            table_with_bound = format_prob_table(probs_with_bound)
        except Exception as ex:
            ctx["error"] = f"Error (con fronteras): {ex}"
            return render(request, "ngram/ngrams_mle.html", ctx)

        ctx["result"] = {
            "n": n,
            "tokens_no_bound": tokens,
            "tokens_with_bound": tokens_with_bounds,
            "probs_no_bound": table_no_bound,
            "probs_with_bound": table_with_bound
        }
    return render(request, "ngram/ngrams_mle.html", ctx)
