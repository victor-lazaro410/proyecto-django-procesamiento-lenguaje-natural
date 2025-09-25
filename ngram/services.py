
import re
from collections import Counter
from typing import List, Tuple, Dict

TOKEN_RE = re.compile(r"<\/?s>|[\wáéíóúñüÁÉÍÓÚÑÜ]+|[\.\!\?]", flags=re.UNICODE)

def default_simple_tokenize(text: str) -> List[str]:
    if not isinstance(text, str):
        text = str(text or "")
    text = text.strip().lower()
    return [t for t in TOKEN_RE.findall(text) if t]

def _split_sentences(tokens: List[str]) -> List[List[str]]:
    sents, cur = [], []
    for t in tokens:
        if t in {".", "!", "?"}:
            if cur:
                sents.append(cur); cur = []
        else:
            cur.append(t)
    if cur:
        sents.append(cur)
    return sents

def add_sentence_boundaries(sent_tokens: List[List[str]]) -> List[str]:
    out = []
    for s in sent_tokens:
        out.extend(["<s>", "<s>"] + s + ["</s>"])
    return out

def generate_ngrams_from_tokens(tokens: List[str], n: int) -> List[Tuple[str, ...]]:
    if not isinstance(n, int) or n < 1:
        raise ValueError("n debe ser >= 1")
    if n == 1:
        return [(t,) for t in tokens]
    N = len(tokens)
    return [tuple(tokens[i:i+n]) for i in range(0, max(0, N - n + 1))]

def ngram_frequencies(tokens: List[str], n: int, join_with: str = " ") -> List[Tuple[str, int]]:
    """ Devuelve lista [("token1 token2", conteo), ...] ordenada desc por conteo. """
    ngrams = generate_ngrams_from_tokens(tokens, n)
    c = Counter(ngrams)
    items = [(join_with.join(ng), cnt) for ng, cnt in c.items()]
    items.sort(key=lambda kv: (-kv[1], kv[0]))
    return items

def mle_conditional_probabilities(tokens: List[str], n: int) -> Dict[Tuple[str, ...], float]:
    """ Devuelve P(w|h) para todos los n-gramas (n>=2). Para n=1 devuelve frecuencias relativas. """
    if n <= 1:
        uni = Counter(tokens)
        total = sum(uni.values()) or 1
        return {(w,): c/total for w, c in uni.items()}
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
