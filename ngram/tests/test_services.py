import pytest
from ngram.services import generate_ngrams_from_tokens, ngram_frequencies, default_simple_tokenize

def test_generate_ngrams_basic():
    tokens = ["a", "b", "c", "d"]
    result = generate_ngrams_from_tokens(tokens, 2)
    assert result == [("a","b"), ("b","c"), ("c","d")]

def test_generate_ngrams_short_list():
    tokens = ["a"]
    result = generate_ngrams_from_tokens(tokens, 2)
    assert result == []

def test_generate_ngrams_invalid_n():
    with pytest.raises(ValueError):
        generate_ngrams_from_tokens(["a","b"], 1)

def test_ngram_frequencies_counts():
    tokens = ["a", "a", "b"]
    freqs = ngram_frequencies(tokens, 2)
    # "a a" y "a b"
    assert freqs["a a"] == 1
    assert freqs["a b"] == 1

def test_default_simple_tokenize():
    text = "Hola, mundo! Hola?"
    tokens = default_simple_tokenize(text)
    assert tokens == ["hola", "mundo", "hola"]