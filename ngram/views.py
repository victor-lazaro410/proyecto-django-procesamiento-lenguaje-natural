import json
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from pathlib import Path

def get_preset_corpora():
    """
    Devuelve un dict con corpus de ejemplo para precargar desde la UI.
    Claves: 'literario', 'tecnico'. Cada entrada: {'label': 'Texto literario'|'Texto técnico', 'text': '...'}
    """
    base = Path(__file__).resolve().parents[1] / "docs"
    data = {}
    try:
        txt = (base / "corpus_julieta_fierro.txt").read_text(encoding="utf-8")
    except Exception:
        txt = ""
    data["literario"] = {"label": "Texto literario", "text": txt}
    try:
        txt2 = (base / "corpus_tecnico_algoritmos.txt").read_text(encoding="utf-8")
    except Exception:
        txt2 = ""
    data["tecnico"] = {"label": "Texto técnico", "text": txt2}
    return data

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
        # Fallback al preset seleccionado si el textarea está vacío
        if not text:
            choice = request.POST.get("corpus_choice")
            presets = get_preset_corpora()
            if choice in presets and presets[choice].get("text"):
                text = presets[choice]["text"]
        if not text:
            choice = request.POST.get("corpus_choice")
            presets = get_preset_corpora()
            if choice in presets and presets[choice]:
                text = presets[choice]

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

    ctx.setdefault("preset_corpora", get_preset_corpora()); ctx.setdefault("default_corpus_choice", "julieta"); ctx.setdefault("preset_corpora", get_preset_corpora()); ctx.setdefault("default_corpus_choice", "literario"); return render(request, "ngram/ngrams.html", context)

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
        # Fallback al preset seleccionado si el textarea está vacío
        if not text:
            choice = request.POST.get("corpus_choice")
            presets = get_preset_corpora()
            if choice in presets and presets[choice].get("text"):
                text = presets[choice]["text"]
        if not text:
            choice = request.POST.get("corpus_choice")
            presets = get_preset_corpora()
            if choice in presets and presets[choice]:
                text = presets[choice]
        # Manejo de archivo subido (txt)
        uploaded_file = request.FILES.get("corpus_file")
        if uploaded_file and uploaded_file.name.endswith(".txt"):
            try:
                text = uploaded_file.read().decode("utf-8")
            except Exception:
                ctx["error"] = "No se pudo leer el archivo de texto. Asegúrate que sea UTF-8."
                ctx.setdefault("preset_corpora", get_preset_corpora()); ctx.setdefault("default_corpus_choice", "julieta"); ctx.setdefault("preset_corpora", get_preset_corpora()); ctx.setdefault("default_corpus_choice", "literario"); ctx.pop('comparison', None); return render(request, "ngram/ngrams_mle.html", ctx)

        n_str = request.POST.get("n", "2")
        try:
            n = int(n_str)
            if n < 2:
                raise ValueError("n debe ser >= 2")
        except Exception:
            ctx["error"] = "Debes indicar un entero n >= 2."
            ctx.setdefault("preset_corpora", get_preset_corpora()); ctx.setdefault("default_corpus_choice", "julieta"); ctx.setdefault("preset_corpora", get_preset_corpora()); ctx.setdefault("default_corpus_choice", "literario"); ctx.pop('comparison', None); return render(request, "ngram/ngrams_mle.html", ctx)

        # Tokenización
        # Bandera para usar fronteras de oración <s> y </s>
        flag = (request.POST.get('usar_fronteras') or request.GET.get('usar_fronteras'))
        if flag is None:
            usar_fronteras = True
        else:
            usar_fronteras = str(flag).strip().lower() in {'1', 'true', 'on', 'sí', 'si', 'yes', 'y'}

        tokens = _maybe_use_project_tokenizer(text)

        # Caso 1: sin fronteras
        try:
            probs_no_bound = mle_conditional_probabilities(tokens, n)
            table_no_bound = format_prob_table(probs_no_bound)
        except Exception as ex:
            ctx["error"] = f"Error (sin fronteras): {ex}"
            ctx.setdefault("preset_corpora", get_preset_corpora()); ctx.setdefault("default_corpus_choice", "julieta"); ctx.setdefault("preset_corpora", get_preset_corpora()); ctx.setdefault("default_corpus_choice", "literario"); 
        # --- Comparación MLE: A = preset seleccionado; B = texto subido/personalizado ---
        choice = request.POST.get("corpus_choice") or ctx.get("default_corpus_choice", "literario")
        presets = get_preset_corpora()
        preset_label = presets.get(choice, {}).get("label", "Corpus seleccionado")
        preset_text = presets.get(choice, {}).get("text", "")

        custom_text = text

        tokens_preset = _maybe_use_project_tokenizer(preset_text)
        tokens_custom = _maybe_use_project_tokenizer(custom_text)

        if n < 2:
            raise ValueError("n debe ser >= 2")

        # Caso sin/ con fronteras para ambos
        try:
            probs_preset = mle_conditional_probabilities(tokens_preset if not usar_fronteras else add_sentence_boundaries(_split_sentences(tokens_preset)), n)
            table_a = format_prob_table(probs_preset)
        except Exception as e:
            table_a = []
            ctx["error_a"] = f"Error (A): {e}"

        try:
            probs_custom = mle_conditional_probabilities(tokens_custom if not usar_fronteras else add_sentence_boundaries(_split_sentences(tokens_custom)), n)
            table_b = format_prob_table(probs_custom)
        except Exception as e:
            table_b = []
            ctx["error_b"] = f"Error (B): {e}"

        ctx.update({
            "comparison": {
                "a": {"label": preset_label, "choice": choice, "probs": table_a, "size": len(tokens_preset)},
                "b": {"label": "Texto personalizado", "probs": table_b, "size": len(tokens_custom)},
                "n": n,
                "usar_fronteras": usar_fronteras,
            }
        })

        ctx.pop('comparison', None); return render(request, "ngram/ngrams_mle.html", ctx)

        # Caso 2: con fronteras
        try:
            sent_tokens = _split_sentences(text)
            tokens_with_bounds = add_sentence_boundaries(sent_tokens)
            probs_with_bound = mle_conditional_probabilities(tokens_with_bounds, n)
            table_with_bound = format_prob_table(probs_with_bound)
        except Exception as ex:
            ctx["error"] = f"Error (con fronteras): {ex}"
            ctx.setdefault("preset_corpora", get_preset_corpora()); ctx.setdefault("default_corpus_choice", "julieta"); ctx.setdefault("preset_corpora", get_preset_corpora()); ctx.setdefault("default_corpus_choice", "literario"); ctx.pop('comparison', None); return render(request, "ngram/ngrams_mle.html", ctx)

        ctx["result"] = {
            "n": n,
            "tokens_no_bound": tokens,
            "tokens_with_bound": tokens_with_bounds,
            "probs_no_bound": table_no_bound,
            "probs_with_bound": table_with_bound
        }
    ctx.setdefault("preset_corpora", get_preset_corpora()); ctx.setdefault("default_corpus_choice", "julieta"); ctx.setdefault("preset_corpora", get_preset_corpora()); ctx.setdefault("default_corpus_choice", "literario"); ctx.pop('comparison', None); return render(request, "ngram/ngrams_mle.html", ctx)


# === Autocompletar con n-gramas (MLE) ===
from django import forms
try:
    from lenguaje_natural.models import DocumentoLN
except Exception:
    DocumentoLN = None

class AutocompleteForm(forms.Form):
    contexto = forms.CharField(
        label="Texto de entrada (contexto)",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False
    )
    archivo = forms.FileField(label="O subir archivo .txt", required=False)
    n = forms.ChoiceField(label="Orden del n-grama", choices=[("1","1 (unigramas)"),("2","2 (bigramas)"),("3","3 (trigramas)")], initial="2")
    usar_fronteras = forms.BooleanField(label="Activar fronteras de oración <s> y </s>", required=False, initial=True)
    corpus_id = forms.ChoiceField(label="Corpus", required=False)
def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        opciones = [("", "— Texto personalizado (escribir o subir .txt) —")]
        if DocumentoLN:
            try:
                qs = DocumentoLN.objects.order_by("-created_at")[:50]
                for doc in qs:
                    opciones.append((str(doc.id), f"{doc.nombre_original or os.path.basename(doc.archivo.name)} ({doc.created_at:%Y-%m-%d})"))
            except Exception:
                pass
        self.fields["corpus_id"].choices = opciones
        self.fields["contexto"].widget.attrs.update({"placeholder": "Escribe aquí tu texto parcial, por ejemplo: 'el perro'"})
        self.fields["contexto"].widget.attrs["required"] = False

# Tokenizador básico y utilidades locales (no dependemos de servicios truncados)
import re
def simple_tokenize(text: str):
    if not text:
        return []
    # minúsculas, separar por no-letras, preservar <s> y </s>
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    # Tokenización rústica por palabras con tildes y dígitos
    toks = re.findall(r"<\/?s>|[\wáéíóúñü]+|[\.\!\?]", text, flags=re.IGNORECASE)
    # Quitar puntos sueltos del final de oración (se usarán para split opcional simple)
    return [t for t in toks if t]

def split_sentences(tokens):
    # dividir por ., !, ? simples
    sents, cur = [], []
    for t in tokens:
        if t in {".","!","?"}:
            if cur:
                sents.append(cur); cur=[]
        else:
            cur.append(t)
    if cur:
        sents.append(cur)
    return sents

def add_sentence_boundaries(sent_tokens):
    with_bounds = []
    for sent in sent_tokens:
        with_bounds.extend(["<s>", "<s>"] + sent + ["</s>"])
    return with_bounds

from collections import Counter

def ngram_counts(tokens, n):
    if n == 1:
        # unigrama: contamos palabras
        return Counter(tokens)
    return Counter(tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1))

def mle_next_word_probs(tokens, n, history):
    """ Devuelve dict {palabra: prob} para la siguiente palabra, según MLE. """
    if n <= 1:
        # Sugerir por frecuencia absoluta (unigrama)
        uni = ngram_counts(tokens, 1)
        total = sum(uni.values()) or 1
        return {w: c/total for w,c in uni.items()}
    # Para n >= 2
    ngrams = ngram_counts(tokens, n)
    prefix_counts = Counter(tuple(tokens[i:i+n-1]) for i in range(len(tokens)-n+2))
    # Filtrar n-gramas que empatan con el history
    cand = {}
    for ng, c in ngrams.items():
        if ng[:-1] == history:
            denom = prefix_counts.get(history, 0)
            if denom > 0:
                cand[ng[-1]] = c/denom
    return cand


def autocomplete_view(request: HttpRequest) -> HttpResponse:
    ctx = {}
    if request.method == "POST":
        form = AutocompleteForm(request.POST, request.FILES)
        if form.is_valid():
            # 1) Entradas
            contexto = form.cleaned_data.get("contexto", "") or ""
            archivo = form.cleaned_data.get("archivo")
            if archivo:
                try:
                    contexto = archivo.read().decode("utf-8", errors="ignore").strip()
                except Exception:
                    try:
                        contexto = archivo.read().decode("latin-1", errors="ignore").strip()
                    except Exception:
                        pass
            n = int(form.cleaned_data.get("n", 2))
            usar_fronteras = bool(form.cleaned_data.get("usar_fronteras"))
            corpus_id = (form.cleaned_data.get("corpus_id") or "").strip()

            # 2) Construir corpus base
            corpus_text = ""
            if corpus_id and corpus_id.startswith("fs:"):
                try:
                    from django.conf import settings
                    import os
                    base_media = getattr(settings, "MEDIA_ROOT", None) or os.path.join(settings.BASE_DIR, "media")
                    fpath = os.path.join(base_media, "lenguaje", corpus_id.split(":", 1)[1])
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                        corpus_text = fh.read()
                except Exception as ex:
                    ctx["error"] = f"No se pudo leer el corpus del sistema de archivos: {ex}"
            elif corpus_id and DocumentoLN:
                try:
                    doc = DocumentoLN.objects.get(id=int(corpus_id))
                    fpath = doc.archivo.path
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                        corpus_text = fh.read()
                except Exception as ex:
                    ctx["error"] = f"No se pudo leer el corpus seleccionado: {ex}"
            if not corpus_text:
                # fallback: usar el propio contexto como mini corpus
                corpus_text = contexto or ""

            # 3) Tokenización con y sin fronteras
            tokens_no_bound = simple_tokenize(corpus_text)
            tokens_with_bound = add_sentence_boundaries(split_sentences(simple_tokenize(corpus_text)))

            # 4) History segun contexto
            ctx_tokens_nb = simple_tokenize(contexto)
            hist_nb = tuple(ctx_tokens_nb[-(n-1):]) if n >= 2 and len(ctx_tokens_nb) >= (n-1) else tuple(ctx_tokens_nb)

            ctx_tokens_wb = add_sentence_boundaries(split_sentences(simple_tokenize(contexto)))
            hist_wb = tuple(ctx_tokens_wb[-(n-1):]) if n >= 2 and len(ctx_tokens_wb) >= (n-1) else tuple(ctx_tokens_wb)

            # 5) Probabilidades MLE para siguiente palabra
            probs_no_bound = mle_next_word_probs(tokens_no_bound, n, hist_nb)
            probs_with_bound = mle_next_word_probs(tokens_with_bound, n, hist_wb)

            # 6) Tablas completas (para mostrar) y top-k
            full_nb = format_prob_table(mle_conditional_probabilities(tokens_no_bound, n), join_with=" ")
            full_wb = format_prob_table(mle_conditional_probabilities(tokens_with_bound, n), join_with=" ")

            tabla_nb = sorted([(w, p) for (w, p) in probs_no_bound.items() if w not in ("<s>", "</s>")], key=lambda kv: (-kv[1], kv[0]))
            tabla_wb = sorted(probs_with_bound.items(), key=lambda kv: (-kv[1], kv[0]))
            sugerencia = (tabla_nb[0][0] if tabla_nb else (tabla_wb[0][0] if tabla_wb else "(sin sugerencia)"))

            ctx["form"] = form
            ctx["resultado"] = {
                "n": n,
                "usar_fronteras": usar_fronteras,
                "history": list(hist_wb),
                "sugerencia": sugerencia,
                "probs_no_bound": tabla_nb,
                "probs_with_bound": tabla_wb,
                "full_no_bound": full_nb,
                "full_with_bound": full_wb,
                "num_tokens_corpus": len(tokens_no_bound),
            }

            # 7) Comparación de textos (Literario vs Personalizado) para NB/WB — se mantiene Autocomplete con/ sin fronteras
            try:
                presets = get_preset_corpora()
                choice = (request.POST.get("corpus_choice") or "").strip() or "literario"
                preset = presets.get(choice) or next(iter(presets.values()), {})
                preset_label = preset.get("label", "Texto literario")
                preset_text = preset.get("text", "") or ""
                custom_text = corpus_text or contexto or ""

                tokens_preset_nb = simple_tokenize(preset_text)
                tokens_custom_nb = simple_tokenize(custom_text)
                tokens_preset_wb = add_sentence_boundaries(split_sentences(tokens_preset_nb))
                tokens_custom_wb = add_sentence_boundaries(split_sentences(tokens_custom_nb))

                from .services import mle_conditional_probabilities as _mle, format_prob_table as _fmt

                ctx["comparison_nb"] = {
                    "a": {"label": preset_label, "probs": _fmt(_mle(tokens_preset_nb, n)), "size": len(tokens_preset_nb)},
                    "b": {"label": "Texto personalizado", "probs": _fmt(_mle(tokens_custom_nb, n)), "size": len(tokens_custom_nb)},
                    "n": n,
                }
                ctx["comparison_wb"] = {
                    "a": {"label": preset_label, "probs": _fmt(_mle(tokens_preset_wb, n)), "size": len(tokens_preset_wb)},
                    "b": {"label": "Texto personalizado", "probs": _fmt(_mle(tokens_custom_wb, n)), "size": len(tokens_custom_wb)},
                    "n": n,
                }
            except Exception as _ex:
                ctx.setdefault("error_comparison", str(_ex))

            ctx.setdefault("preset_corpora", get_preset_corpora())
            ctx.setdefault("default_corpus_choice", "literario")
            return render(request, "ngram/autocomplete.html", ctx)
        else:
            ctx["form"] = form
            ctx.setdefault("preset_corpora", get_preset_corpora())
            ctx.setdefault("default_corpus_choice", "literario")
            return render(request, "ngram/autocomplete.html", ctx)
    else:
        ctx["form"] = AutocompleteForm(initial={"n": "2", "usar_fronteras": True})
        ctx.setdefault("preset_corpora", get_preset_corpora())
        ctx.setdefault("default_corpus_choice", "literario")
        return render(request, "ngram/autocomplete.html", ctx)
