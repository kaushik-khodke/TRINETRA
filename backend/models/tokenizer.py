"""
TRINETRA — Versioned Deterministic Text Tokenizer for Remote Sensing VQA & Grounding
Module: backend/models/tokenizer.py

Implements Stage 7 Tokenizer Governance:
1. Versioned VqaTokenizer (v2.0.0) with validated vocabulary size.
2. Supports verified word2idx vocabulary dictionaries (e.g. RSVQA vocabulary).
3. Cryptographic SHA-256 fallback mapping for out-of-vocabulary words.
4. Strictly eliminates Python's runtime hash() non-determinism.
5. Checkpoint embedding compatibility validation.
"""

import os
import json
import hashlib
from typing import List, Dict, Optional, Any, Union


def deterministic_word_hash(word: str, vocab_size: int = 5000, offset: int = 100) -> int:
    """
    Computes a deterministic token ID in [offset, vocab_size - 1] from a word string.
    Unlike Python's built-in hash(), this produces identical integer IDs across all
    Python sessions, operating systems, and environments via SHA-256 digest truncation.
    """
    clean_word = word.strip().lower()
    if not clean_word:
        return 0  # PAD token
    digest = hashlib.sha256(clean_word.encode("utf-8")).hexdigest()
    int_val = int(digest[:8], 16)
    range_size = max(1, vocab_size - offset)
    return (int_val % range_size) + offset


class VqaTokenizer:
    """
    Versioned, auditable text tokenizer for Remote Sensing VQA.
    Guarantees stable token IDs across train, test, and live inference.
    """
    VERSION = "2.0.0"

    def __init__(
        self,
        vocab_size: int = 5000,
        max_length: int = 16,
        offset: int = 100,
        vocab_path: Optional[str] = None,
        word2idx: Optional[Dict[str, int]] = None
    ):
        self.version = self.VERSION
        self.vocab_size = vocab_size
        self.max_length = max_length
        self.offset = offset
        self.pad_token_id = 0
        self.unk_token_id = 1

        self.word2idx: Dict[str, int] = {}
        self.idx2word: Dict[int, str] = {0: "<pad>", 1: "<unk>"}

        if word2idx is not None:
            self._set_vocabulary(word2idx)
        elif vocab_path and os.path.exists(vocab_path):
            self.load_vocabulary(vocab_path)

    def _set_vocabulary(self, word2idx: Dict[str, int]):
        self.word2idx = {str(k).lower(): int(v) for k, v in word2idx.items()}
        self.idx2word = {int(v): str(k).lower() for k, v in word2idx.items()}
        self.idx2word[0] = "<pad>"
        self.idx2word[1] = "<unk>"

    def load_vocabulary(self, vocab_path: str) -> int:
        """Loads official question or answer vocabulary from JSON manifest."""
        if not os.path.exists(vocab_path):
            raise FileNotFoundError(f"Vocabulary file not found: {vocab_path}")

        with open(vocab_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle various vocabulary formats (word2idx, questions_vocab, etc.)
        if "word2idx" in data:
            vocab = data["word2idx"]
        elif "vocab" in data:
            vocab = data["vocab"]
        elif "ans2idx" in data and not "word2idx" in data:
            # If answer vocab is loaded, map words
            vocab = data["ans2idx"]
        else:
            vocab = data

        self._set_vocabulary(vocab)
        return len(self.word2idx)

    load_vocab = load_vocabulary

    def get_vocab_size(self) -> int:
        """Returns vocabulary size from loaded dictionary or configured bound."""
        return len(self.word2idx) if self.word2idx else self.vocab_size

    def tokenize(self, text: str, max_length: Optional[int] = None) -> List[int]:
        """
        Tokenizes text string into fixed-length integer token ID list with zero-padding.
        Uses verified dictionary first; falls back to deterministic SHA-256 hash.
        """
        ml = max_length or self.max_length
        cleaned = text.lower().replace("?", "").replace(",", "").replace(".", "").replace("!", "").replace(";", "").replace(":", "")
        words = cleaned.split()

        tokens = []
        for w in words[:ml]:
            if w in self.word2idx:
                token_id = self.word2idx[w]
            else:
                # Deterministic SHA-256 hash strictly inside [offset, vocab_size - 1]
                token_id = deterministic_word_hash(w, vocab_size=self.vocab_size, offset=self.offset)

            # Ensure within vocab bounds
            token_id = min(token_id, self.vocab_size - 1)
            tokens.append(token_id)

        # Zero-pad to max_length
        while len(tokens) < ml:
            tokens.append(self.pad_token_id)

        return tokens

    encode = tokenize

    def decode(self, token_ids: List[int]) -> str:
        """Decodes token IDs back to word sequence, omitting padding."""
        words = []
        for tid in token_ids:
            if tid == self.pad_token_id:
                continue
            if tid in self.idx2word:
                words.append(self.idx2word[tid])
            else:
                words.append(f"<tok_{tid}>")
        return " ".join(words)

    def validate_compatibility(self, embedding_vocab_size: Optional[int] = None, model_vocab_size: Optional[int] = None) -> bool:
        """
        Verifies that tokenizer output will not cause index out-of-bounds in neural embedding layer.
        """
        target_size = embedding_vocab_size if embedding_vocab_size is not None else model_vocab_size
        if target_size is None:
            raise ValueError("Must provide either embedding_vocab_size or model_vocab_size")
        
        effective_size = len(self.word2idx) if self.word2idx else self.vocab_size
        if effective_size > target_size:
            raise ValueError(
                f"Vocabulary size mismatch: Tokenizer configured for {effective_size} tokens, "
                f"but model embedding layer supports only {target_size} tokens."
            )
        return True


def tokenize_sequence(text: str, max_length: int = 16, vocab_size: int = 5000, offset: int = 100) -> List[int]:
    """
    Backwards-compatible standalone tokenization function using SHA-256 word hashing.
    """
    tokenizer = VqaTokenizer(vocab_size=vocab_size, max_length=max_length, offset=offset)
    return tokenizer.tokenize(text)
