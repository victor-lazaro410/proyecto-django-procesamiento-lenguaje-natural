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