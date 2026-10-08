"""CTC alternatives must retain visual likelihood, including repeated digits."""
from collections import defaultdict
from itertools import product
import math

import numpy as np
import pytest

from app.ocr.crnn_provider import CrnnOcrProvider


def provider(vocab):
    instance = object.__new__(CrnnOcrProvider)
    instance._inv_vocab = vocab
    return instance


def test_beam_matches_enumerated_paths_without_rewriting_repeated_digits():
    probabilities = np.array([[.1, .8, .1], [.7, .2, .1],
                              [.1, .8, .1], [.6, .1, .3]])
    exact = defaultdict(float)
    for path in product(range(3), repeat=4):
        text, previous = [], None
        for value in path:
            if value and value != previous:
                text.append({1: '0', 2: '5'}[value])
            previous = value
        exact[''.join(text)] += math.prod(probabilities[t, value] for t, value in enumerate(path))
    actual = provider({1: '0', 2: '5'})._decode_ctc_beam_search(
        probabilities, beam_width=1000, top_k=1000)
    assert {row['text'] for row in actual} == set(exact)
    for row in actual:
        assert row['logProb'] == pytest.approx(math.log(exact[row['text']]), abs=.00006)
    assert actual[0]['text'] == '00'  # No conversion to one zero or to a solved value.


def test_long_low_probability_sequences_do_not_underflow_or_share_a_floor():
    probabilities = np.full((400, 17), 1 / 17, dtype=np.float64)
    actual = provider({i: str(i % 10) for i in range(1, 17)})._decode_ctc_beam_search(
        probabilities, beam_width=15, top_k=5)
    assert len(actual) == 5
    assert all(math.isfinite(row['logProb']) and row['logProb'] < -700 for row in actual)
    assert all(0 < row['normalizedScore'] < 1 for row in actual)
    assert [row['logProb'] for row in actual] == sorted(
        [row['logProb'] for row in actual], reverse=True)


def test_small_nonzero_blank_probability_keeps_repeated_digit_path():
    probabilities = np.array([[0., 1.], [1e-8, 1 - 1e-8], [0., 1.]])
    actual = provider({1: '7'})._decode_ctc_beam_search(probabilities, top_k=5)
    by_text = {row['text']: row for row in actual}
    assert by_text['77']['logProb'] == pytest.approx(math.log(1e-8), abs=.00006)
    assert by_text['7']['logProb'] == pytest.approx(math.log(1 - 1e-8), abs=.00006)
