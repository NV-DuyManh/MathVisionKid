"""CPU-only contract tests for memory-saving microbatch updates."""
import pytest

torch = pytest.importorskip("torch", reason="CPU PyTorch is required for loss-equivalence checks")

from t4_microbatch_optimization import (  # noqa: E402
    partition_microbatches,
)
from t4_microbatch_optimization_v2 import (  # noqa: E402
    per_example_mean_cross_entropy,
    selected_per_example_mean_cross_entropy,
    supervised_prediction_positions,
)


def test_loss_is_mean_of_per_example_token_means_after_causal_shift():
    # Example 0 has one supervised target with high loss. Example 1 has three
    # easy targets. A flattened token mean would overweight example 1.
    logits = torch.tensor([
        [[0.0, 2.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]],
        [[0.0, 2.0], [0.0, 2.0], [0.0, 2.0], [0.0, 0.0]],
    ], dtype=torch.float32, device="cpu")
    labels = torch.tensor([
        [-100, 0, -100, -100],
        [-100, 1, 1, 1],
    ], dtype=torch.long, device="cpu")

    actual = per_example_mean_cross_entropy(logits, labels, ignore_index=-100)
    shifted_logits = logits[:, :-1].reshape(-1, logits.shape[-1])
    shifted_labels = labels[:, 1:].reshape(-1)
    token_losses = torch.nn.functional.cross_entropy(
        shifted_logits, shifted_labels, ignore_index=-100, reduction="none")
    mask = shifted_labels.ne(-100)
    per_row = token_losses.reshape(2, 3)
    row_mask = mask.reshape(2, 3)
    expected = torch.stack([
        per_row[i][row_mask[i]].mean() for i in range(2)
    ]).mean()
    flat_token_average = token_losses[mask].mean()

    assert torch.isfinite(actual)
    assert torch.allclose(actual, expected, rtol=1e-6, atol=1e-7)
    assert not torch.allclose(actual, flat_token_average, rtol=1e-3, atol=1e-4)


def test_microbatches_preserve_optimizer_group_boundaries_order_and_tail():
    # The runtime keeps the optimizer group at 16 examples. A 4-example
    # microbatch schedule must cover both complete groups and the final tail.
    all_items = list(range(35))
    optimizer_groups = [all_items[i:i + 16] for i in range(0, len(all_items), 16)]
    assert [len(group) for group in optimizer_groups] == [16, 16, 3]

    grouped_microbatches = [
        partition_microbatches(group, microbatch_size=4)
        for group in optimizer_groups
    ]
    assert [[len(microbatch) for microbatch in group] for group in grouped_microbatches] == [
        [4, 4, 4, 4], [4, 4, 4, 4], [3]
    ]
    assert [item for group in grouped_microbatches for microbatch in group for item in microbatch] == all_items
    assert len(grouped_microbatches) == len(optimizer_groups)


@pytest.mark.parametrize("microbatch_size", [0, -1])
def test_microbatch_size_must_be_positive(microbatch_size):
    with pytest.raises(ValueError):
        partition_microbatches([1, 2], microbatch_size=microbatch_size)


def test_sparse_supervised_positions_preserve_loss_and_gradient_with_single_eot():
    # Row 0 supervises positions 0 and 3; row 1 supervises 1, 2 and 3.
    # The last target in each row is the single EOT-like target.
    labels = torch.tensor([
        [-100, 0, -100, -100, 1],
        [-100, -100, 1, 0, 1],
    ], dtype=torch.long, device="cpu")
    expected_positions = torch.tensor([0, 1, 2, 3], dtype=torch.long)
    positions = supervised_prediction_positions(labels, ignore_index=-100)
    assert torch.equal(positions, expected_positions)

    torch.manual_seed(17)
    dense_logits = torch.randn(2, 5, 3, dtype=torch.float64, requires_grad=True)
    dense_loss = per_example_mean_cross_entropy(dense_logits, labels, ignore_index=-100)
    dense_loss.backward()
    dense_gradient = dense_logits.grad.detach().clone()

    sparse_source = dense_logits.detach().clone().requires_grad_(True)
    selected_logits = sparse_source[:, :-1].index_select(dim=1, index=positions)
    aligned_targets = labels.index_select(dim=1, index=positions + 1)
    sparse_loss = selected_per_example_mean_cross_entropy(
        selected_logits, aligned_targets, ignore_index=-100)
    sparse_loss.backward()

    assert torch.allclose(sparse_loss, dense_loss.detach(), rtol=1e-10, atol=1e-12)
    assert torch.allclose(sparse_source.grad, dense_gradient, rtol=1e-10, atol=1e-12)
    assert torch.equal(aligned_targets.ne(-100).sum(dim=1), labels[:, 1:].ne(-100).sum(dim=1))


def test_sparse_positions_reject_empty_supervision():
    labels = torch.full((2, 4), -100, dtype=torch.long)
    with pytest.raises(ValueError):
        supervised_prediction_positions(labels, ignore_index=-100)
