"""Unit tests for CTC greedy decoding, blank token handling, and repeat character collapse."""
import numpy as np
import pytest


def greedy_decode(preds: np.ndarray, inv_vocab: dict, blank_idx: int = 0) -> str:
    out = []
    prev = -1
    for idx in preds:
        if idx != blank_idx and idx != prev:
            out.append(inv_vocab.get(int(idx), "?"))
        prev = idx
    return "".join(out)


def test_greedy_decode_simple():
    vocab = {"<blank>": 0, "a": 1, "b": 2, "c": 3}
    inv_vocab = {v: k for k, v in vocab.items()}

    # Sequence with repeated tokens separated by blanks: a, blank, a -> "aa"
    # a, a, a -> "a"
    preds = np.array([1, 1, 1, 0, 2, 2, 0, 3])
    decoded = greedy_decode(preds, inv_vocab, blank_idx=0)
    assert decoded == "abc"


def test_greedy_decode_with_blanks():
    vocab = {"<blank>": 0, "1": 1, "+": 2, "2": 3, "=": 4, "3": 5}
    inv_vocab = {v: k for k, v in vocab.items()}

    # 1, 1, blank, +, blank, 2, 2, =, 3
    preds = np.array([0, 1, 1, 0, 2, 0, 3, 3, 4, 5, 0])
    decoded = greedy_decode(preds, inv_vocab, blank_idx=0)
    assert decoded == "1+2=3"


def test_greedy_decode_all_blank():
    vocab = {"<blank>": 0, "a": 1}
    inv_vocab = {v: k for k, v in vocab.items()}

    preds = np.array([0, 0, 0, 0, 0])
    decoded = greedy_decode(preds, inv_vocab, blank_idx=0)
    assert decoded == ""
