"""Reusable inference-only request helper; model/runtime dependencies load lazily."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import time
from typing import Any

import behavior_renderer as B
import fewshot_contract as F
import inference_contract as I

LEGAL_MODES = ("worked_solution", "hint_level_1", "hint_level_2", "hint_level_3")
SELECTION_VALUES = ("fewshot_contract", "inference_contract")
UNVALIDATED_FEWSHOT_MODES = {"hint_level_2", "hint_level_3"}
MAX_PROMPT_TOKENS = 3072
MAX_NEW_TOKENS = 1024
SELECTION_SCHEMA = "MathVisionKid.mode_context_selection.v1"
SELECTION_PATH = F.ROOT / "fewshot_selection.json"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_selection(selection: dict[str, Any]) -> tuple[dict[str, str], str]:
    """Require a frozen whole-mode selection; only known policies are accepted."""
    if not isinstance(selection, dict) or selection.get("schema") != SELECTION_SCHEMA:
        raise ValueError("Unexpected mode-context selection schema")
    if selection.get("selected_before_final_test") is not True:
        raise ValueError("Selection must be frozen before final-test use")
    if selection.get("base_kind") != "untrained_base" or selection.get("production_approval") is not False:
        raise ValueError("Selection is not approved for this untrained-base inference artifact")
    modes = selection.get("mode_selection")
    if not isinstance(modes, dict) or set(modes) != set(LEGAL_MODES):
        raise ValueError("Selection must define exactly the four supported modes")
    if any(value not in SELECTION_VALUES for value in modes.values()):
        raise ValueError("Unknown mode selection value")
    eligible = selection.get("eligible_by_model_mode")
    if not isinstance(eligible, dict) or set(eligible) != set(LEGAL_MODES) or any(type(v) is not bool for v in eligible.values()):
        raise ValueError("Eligibility must define booleans for exactly the four supported modes")
    frozen = {mode: modes[mode] for mode in LEGAL_MODES}
    if any(frozen[mode] == "fewshot_contract" and not eligible[mode] for mode in LEGAL_MODES):
        raise ValueError("Few-shot mode is not marked eligible")
    if any(frozen[mode] == "fewshot_contract" for mode in UNVALIDATED_FEWSHOT_MODES) or any(eligible[mode] for mode in UNVALIDATED_FEWSHOT_MODES):
        raise ValueError("Few-shot selection is not validated for hint levels 2 or 3")
    bank_sha = _sha(F.BANK_PATH.read_bytes())
    if selection.get("bank_sha256") != bank_sha:
        raise ValueError("Selection example-bank SHA256 mismatch")
    expected_modules = selection.get("inference_module_sha256")
    actual_modules = {
        "fewshot_contract": _sha(Path(F.__file__).read_bytes()),
        "inference_contract": _sha(Path(I.__file__).read_bytes()),
    }
    if expected_modules != actual_modules:
        raise ValueError("Selection inference-module SHA256 mismatch")
    if not SELECTION_PATH.is_file():
        raise ValueError("Frozen selection artifact is missing")
    frozen_artifact = json.loads(SELECTION_PATH.read_bytes())
    if _canonical(frozen_artifact) != _canonical(selection):
        raise ValueError("Provided selection differs from the frozen selection artifact")
    return frozen, _sha(SELECTION_PATH.read_bytes())


def _prepare_messages(problem: str, grade: int, mode: str,
                      selection: dict[str, Any]) -> tuple[list[dict[str, str]], list[str], str]:
    if not isinstance(problem, str) or not problem.strip():
        raise ValueError("Problem must be nonempty text")
    if type(grade) is not int or grade not in range(1, 6):
        raise ValueError("Grade must be an integer from 1 to 5")
    if mode not in LEGAL_MODES:
        raise ValueError("Unsupported tutor mode")
    frozen_modes, selection_sha = validate_selection(selection)
    user = B.prompt({"grade": grade, "problem": problem, "mode": mode})
    messages = [{"role": "system", "content": B.SYSTEM}]
    example_ids: list[str] = []
    if frozen_modes[mode] == "fewshot_contract":
        bank, _ = F.load_and_validate_bank()
        entries = [entry for entry in bank["entries"] if entry["mode"] == mode]
        expected = bank["mode_counts"].get(mode)
        if len(entries) != expected or not entries:
            raise ValueError("Few-shot bank selection is incomplete for requested mode")
        for entry in entries:
            messages.extend((
                {"role": "user", "content": entry["actual_prompt"]},
                {"role": "assistant", "content": entry["actual_target"]},
            ))
            example_ids.append(entry["sample_id"])
    messages.append({"role": "user", "content": user})
    return messages, example_ids, selection_sha


def messages_for_request(problem: str, grade: int, mode: str,
                         selection: dict[str, Any]) -> list[dict[str, str]]:
    """Build only system + optional source demonstrations + intact user request."""
    return _prepare_messages(problem, grade, mode, selection)[0]


def tokenize_request(tok: Any, problem: str, grade: int, mode: str,
                     selection: dict[str, Any], max_prompt_tokens: int = MAX_PROMPT_TOKENS):
    """Tokenize without truncation and return messages, source IDs and prompt hash."""
    if type(max_prompt_tokens) is not int or max_prompt_tokens < 1:
        raise ValueError("Prompt token limit must be a positive integer")
    messages, example_ids, selection_sha = _prepare_messages(problem, grade, mode, selection)
    encoded = tok.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, enable_thinking=False,
    )
    ids = encoded["input_ids"] if hasattr(encoded, "keys") else encoded
    if hasattr(ids, "tolist"):
        ids = ids.tolist()
    if ids and isinstance(ids[0], list):
        ids = ids[0]
    if len(ids) > max_prompt_tokens:
        raise ValueError(f"Prompt too long ({len(ids)} > {max_prompt_tokens}); truncation is forbidden")
    prompt_sha = _sha(_canonical(ids).encode("utf-8"))
    return encoded, messages, example_ids, prompt_sha, selection_sha


def generate_request(model: Any, tok: Any, problem: str, grade: int, mode: str,
                     selection: dict[str, Any], seed: int = 20261024,
                     timeout_seconds: float = 120.0,
                     max_prompt_tokens: int = MAX_PROMPT_TOKENS) -> dict[str, Any]:
    """Generate with Qwen official nonthinking sampling; caller supplies base model/tokenizer."""
    if type(seed) is not int or seed < 0:
        raise ValueError("Seed must be a nonnegative integer")
    if timeout_seconds <= 0:
        raise ValueError("Timeout must be positive")
    _, messages, example_ids, prompt_sha, selection_sha = tokenize_request(
        tok, problem, grade, mode, selection, max_prompt_tokens,
    )
    # Heavy framework imports occur only after validation/token budget checks.
    import torch
    from transformers import GenerationConfig

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    random.seed(seed)
    ids = tok.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, enable_thinking=False,
        return_tensors="pt", return_dict=True,
    ).to("cuda" if torch.cuda.is_available() else "cpu")
    prompt_ids = ids["input_ids"][0].tolist()
    actual_sha = _sha(_canonical(prompt_ids).encode("utf-8"))
    if actual_sha != prompt_sha:
        raise ValueError("Tokenized prompt changed between validation and generation")
    if len(prompt_ids) > max_prompt_tokens:
        raise ValueError("Prompt exceeds token limit; truncation is forbidden")
    decoding = {
        "do_sample": True, "temperature": 0.7, "top_p": 0.8, "top_k": 20,
        "min_p": 0.0, "num_beams": 1, "max_new_tokens": MAX_NEW_TOKENS,
        "repetition_penalty": 1.0, "use_cache": True,
        "eos_token_id": 151645, "pad_token_id": tok.pad_token_id,
    }
    started = time.monotonic()
    with torch.inference_mode():
        result = model.generate(
            **ids, generation_config=GenerationConfig(**decoding),
            max_time=timeout_seconds,
        )
    tokens = result[0, ids["input_ids"].shape[1]:]
    ended_eos = bool(len(tokens) and int(tokens[-1]) == 151645)
    return {
        "output": tok.decode(tokens, skip_special_tokens=True).strip(),
        "ended_eos": ended_eos,
        "possibly_truncated": not ended_eos,
        "generation_seconds": time.monotonic() - started,
        "prompt_token_sha256": actual_sha,
        "protocol": {
            "model": I.MODEL, "revision": I.REVISION,
            "enable_thinking": False, "decoding": decoding,
            "seed": seed, "max_prompt_tokens": max_prompt_tokens,
            "truncation": "forbidden",
        },
        "source_example_ids": example_ids,
        "selection_sha256": selection_sha,
        "prompt_message_count": len(messages),
    }


# Short alias for callers that already own request validation and selection persistence.
generate = generate_request
