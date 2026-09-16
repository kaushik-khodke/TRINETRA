"""
TRINETRA — Deterministic Text Tokenizer for Remote Sensing VQA & Grounding
Provides reproducible word-to-token integer mapping using cryptographic hashing (SHA-256)
to guarantee stability across Python process invocations and platforms.
"""

import hashlib
from typing import List

def deterministic_word_hash(word: str, vocab_size: int = 5000, offset: int = 100) -> int:
    """
    Computes a deterministic token ID in [offset, vocab_size - 1] from a word string.
    Unlike Python's built-in hash(), this produces identical integer IDs across all
    Python sessions, operating systems, and environments.
    """
    clean_word = word.strip().lower()
    if not clean_word:
        return 0  # PAD token
    digest = hashlib.sha256(clean_word.encode("utf-8")).hexdigest()
    int_val = int(digest[:8], 16)
    range_size = max(1, vocab_size - offset)
    return (int_val % range_size) + offset

def tokenize_sequence(text: str, max_length: int = 16, vocab_size: int = 5000, offset: int = 100) -> List[int]:
    """
    Tokenizes a text string into a fixed-length list of deterministic token IDs with zero-padding.
    """
    cleaned = text.lower().replace("?", "").replace(",", "").replace(".", "").replace("!", "").replace(";", "")
    words = cleaned.split()
    tokens = [deterministic_word_hash(w, vocab_size=vocab_size, offset=offset) for w in words[:max_length]]
    while len(tokens) < max_length:
        tokens.append(0)
    return tokens
