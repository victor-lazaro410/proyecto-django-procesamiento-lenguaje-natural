import re
from collections import Counter
from typing import List, Tuple

def generate_ngrams_from_tokens(tokens: List[str], n: int) -> List[Tuple[str, ...]]:
    """
    Genera n-gramas contiguos (n > 1) a partir de una lista de tokens.
    No aplica padding; si len(tokens) < n, devuelve lista vacía.
    """
    if not isinstance(n, int) or n < 2:
        raise ValueError("n debe ser un entero >= 2")
    if not tokens:
        return []
    N = len(tokens)
    return [tuple(tokens[i:i+n]) for i in range(0, max(0, N - n + 1))]

def ngram_frequencies(tokens: List[str], n: int, join_with: str = " ") -> Counter:
    """
    Devuelve un Counter con frecuencias de n-gramas (clave = string del n-grama unido por 'join_with').
    """
    ngrams = generate_ngrams_from_tokens(tokens, n)
    joined = [join_with.join(tup) for tup in ngrams]
    return Counter(joined)

def default_simple_tokenize(text: str) -> List[str]:
    """
    Fallback de tokenización simple (minúsculas, caracteres alfabéticos y dígitos).
    Se intenta integrar con el flujo existente: si el proyecto expone una función `tokenize`,
    se puede invocar desde la vista (ver views.py). Este método sirve como respaldo.
    """
    import re
    if not text:
        return []
    # Sustituye cualquier carácter no alfanumérico por espacios y divide
    text = text.lower()
    tokens = re.findall(r"[a-záéíóúñü0-9]+", text, flags=re.IGNORECASE)
    return tokens

from typing import Dict, Iterable, List, Tuple
from collections import Counter

def _split_sentences(text: str) -> List[List[str]]:
    """Divide el texto en oraciones y tokeniza cada una usando default_simple_tokenize."""
    if not text:
        return []
    raw = re.split(r'[.!?]+', text)
    sents: List[List[str]] = []
    for s in raw:
        toks = default_simple_tokenize(s)
        if toks:
            sents.append(toks)
    return sents

def add_sentence_boundaries(sent_tokens: List[List[str]], bos: str = "<s>", eos: str = "</s>") -> List[str]:
    """Agrega <s> y </s> por oración y aplana."""
    seq: List[str] = []
    for s in sent_tokens:
        seq.extend([bos, *s, eos])
    return seq

def mle_conditional_probabilities(tokens: List[str], n: int) -> Dict[Tuple[str, ...], float]:
    if n < 2:
        raise ValueError("n debe ser >= 2 para probabilidades condicionales")
    n_counts = Counter(tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1))
    prefix_counts = Counter(tuple(tokens[i:i+n-1]) for i in range(len(tokens)-n+2))
    probs: Dict[Tuple[str, ...], float] = {}
    for ng, c in n_counts.items():
        prefix = ng[:-1]
        denom = prefix_counts.get(prefix, 0)
        if denom > 0:
            probs[ng] = c / denom
    return probs

def format_prob_table(probs: Dict[Tuple[str, ...], float], join_with: str = " ") -> List[Tuple[str, float]]:
    items = [(join_with.join(ng), p) for ng, p in probs.items()]
    items.sort(key=lambda kv: (-kv[1], kv[0]))
    return items
