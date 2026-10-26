"""Optional physical batching that preserves the original microbatch-two loss.

Each optimizer group has 16 original rows in eight consecutive original pairs.
Every pair contributes its supervised-token mean CE times 2/16. Physical chunks
may contain two/four whole pairs, without changing that objective. This module
does not alter targets, sample order, padding or optimizer state. No torch import
or runtime/model action occurs at import time. GPU numerical and gradient parity
must be verified against the actual patched model before enabling this path.
"""
from __future__ import annotations


def make_physical_chunks(original_pairs, microbatch, group_rows=16):
    """Return flattened chunks preserving exact original pairs and row order."""
    if microbatch not in (2, 4, 8) or group_rows != 16:
        raise ValueError("supported physical batches are 2/4/8 within a 16-row group")
    pairs = [list(pair) for pair in original_pairs]
    if len(pairs) != group_rows // 2 or any(len(pair) != 2 for pair in pairs):
        raise ValueError("supply the eight original adjacent row pairs")
    per_chunk = microbatch // 2
    return [[row for pair in pairs[start:start+per_chunk] for row in pair]
            for start in range(0, len(pairs), per_chunk)]


def pair_weighted_reference(token_losses, group_rows=16):
    """Pure-Python arithmetic reference; each row supplies real target losses.

    This fixture helper cannot establish model/token alignment or GPU parity.
    Empty individual rows are allowed if their original pair has target tokens.
    """
    if group_rows != 16 or not token_losses or len(token_losses) % 2 or len(token_losses) > group_rows:
        raise ValueError("loss rows must be whole original pairs within one group")
    result = 0.0
    for offset in range(0, len(token_losses), 2):
        pair = list(token_losses[offset]) + list(token_losses[offset+1])
        if not pair:
            raise ValueError("original pair has no supervised target tokens")
        result += sum(pair) / len(pair) * (2.0 / group_rows)
    return result


def causal_keep_positions(labels):
    """Logit time indices j predicting supervised target labels[:, j+1]."""
    import torch
    if labels.ndim != 2 or labels.shape[0] % 2 or labels.shape[0] == 0 or labels.shape[1] < 2:
        raise ValueError("labels must be nonempty paired rows with causal targets")
    if labels.dtype != torch.long:
        raise ValueError("labels must retain torch.long target IDs")
    positions = (labels[:, 1:] != -100).any(dim=0).nonzero(as_tuple=False).flatten()
    if not positions.numel():
        raise ValueError("chunk has no supervised causal targets")
    return positions


def pair_weighted_causal_loss(logits, labels, *, positions, group_rows=16):
    """Reduce selective causal logits with the original pairwise token means.

    `positions` must be exactly causal_keep_positions(labels), and model forward
    must use logits_to_keep=positions (indices into the full input time axis).
    logits[B,K,V] thus predict labels[:,1:].index_select(1,positions), not labels
    at the same full-input positions. This is the single causal shift.
    Returns the chunk contribution already weighted for the complete group;
    caller backpropagates each chunk once and MUST NOT divide by accumulation.
    """
    import torch
    import torch.nn.functional as functional
    if group_rows != 16 or labels.shape[0] not in (2, 4, 8):
        raise ValueError("supported chunks contain 2/4/8 rows of one 16-row group")
    expected = causal_keep_positions(labels)
    if positions.dtype != torch.long or positions.device != labels.device or not torch.equal(positions, expected):
        raise ValueError("positions must retain every and only supervised causal column")
    if logits.ndim != 3 or tuple(logits.shape[:2]) != (labels.shape[0], positions.numel()):
        raise ValueError("selective logits do not align with target batch/positions")
    targets = labels[:, 1:].index_select(1, positions)
    if targets.device != logits.device:
        raise ValueError("logits and targets must be on the same device")
    valid = targets.ne(-100)
    pair_counts = valid.reshape(labels.shape[0] // 2, -1).sum(dim=1)
    if bool(pair_counts.eq(0).any().item()):
        raise ValueError("original pair has no supervised causal targets")
    # Float32 CE is explicit for numerical stability. It can cost significant
    # memory for this vocabulary; benchmark actual T4 feasibility before use.
    token_ce = functional.cross_entropy(logits.float().reshape(-1, logits.shape[-1]),
                                        targets.reshape(-1), reduction="none", ignore_index=-100)
    pair_sums = token_ce.reshape(labels.shape[0] // 2, -1).sum(dim=1)
    return (pair_sums / pair_counts.to(pair_sums.dtype)).sum() * (2.0 / group_rows)


def pair_weighted_forward_loss(model, batch, *, group_rows=16, forward_kwargs=None):
    """Optional adapter: no labels passed to model, preserve supplied batch.

    The caller chooses paired physical chunks and its normal autocast context.
    This function adds no optimizer step, gradient scaling or extra divisor.
    Model support for tensor logits_to_keep and actual GPU gradient parity are
    mandatory caller checks. Unsupported models raise; there is no silent path.
    """
    labels = batch["labels"]
    positions = causal_keep_positions(labels)
    kwargs = dict(forward_kwargs or {})
    if set(kwargs) & {"input_ids", "attention_mask", "labels", "logits_to_keep"}:
        raise ValueError("forward kwargs cannot override targets or alignment")
    output = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"],
                   logits_to_keep=positions, **kwargs)
    return pair_weighted_causal_loss(output.logits, labels, positions=positions, group_rows=group_rows)
