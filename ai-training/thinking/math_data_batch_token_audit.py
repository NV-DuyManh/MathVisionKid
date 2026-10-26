"""Opt-in, bounded exact tokenizer batching for the unchanged v3 CPU scanner.

After an orderly scanner pause::

    adapter = BatchTokenAuditAdapter(audit.tokenizer, batch_size=128)
    with adapter.installed():
        result = adapter.consume(audit, entry, local_path, max_rows=20000)

Only calls made by ``adapter.consume`` in its current thread use the cache.
Other callers retain the original exact tokenizer/payload functions. No data,
recipe, source linkage, scanner implementation, or checkpoint schema changes.
Oversized individual rows use the original exact single-row implementation.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
import json
import threading

import exhaustive_colab_loader as L
import math_data_archive_audit as A
from math_data_candidate_stream import member_key

_ORIGINAL_TOKENIZE = L.tokenize_assistant_only
_ORIGINAL_PAYLOAD = A.payload
_LOCAL = threading.local()
_LOCK = threading.RLock()
_OWNER = None
_ACTIVE = 0


def _row_bytes(row):
    return L.canonical_json(row).encode("utf-8")


class _PreparedTokenizer:
    """Feeds exact official batch outputs through all original row gates."""
    def __init__(self, item, full, offsets):
        self.item, self.full, self.offsets = item, full, offsets

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt,
                            enable_thinking):
        assert enable_thinking is False
        if tokenize:
            assert messages == self.item[1]["messages"] and not add_generation_prompt
            return self.full
        if add_generation_prompt:
            assert messages == self.item[1]["messages"][:2]
            return self.item[3]
        assert messages == self.item[1]["messages"]
        return self.item[4]

    def __call__(self, rendered, *, add_special_tokens, return_offsets_mapping):
        assert rendered == self.item[4]
        assert add_special_tokens is False and return_offsets_mapping is True
        return self.offsets


@dataclass
class _Context:
    adapter: object
    audit: object
    key: str
    start: int
    max_rows: int | None
    cache: dict = field(default_factory=dict)


def _tokenize(row, tokenizer, max_sequence_tokens=40960):
    context = getattr(_LOCAL, "context", None)
    if (context is not None and tokenizer is context.adapter.tokenizer
            and max_sequence_tokens == context.audit.limit):
        try:
            cached = context.cache.get(_row_bytes(row))
        except Exception:
            # Cache bookkeeping is optional. The original exact row path
            # remains authoritative if a key cannot be prepared/looked up.
            context.adapter.stats["cache_key_fallbacks"] += 1
            cached = None
        if cached is not None:
            context.adapter.stats["cache_hits"] += 1
            if isinstance(cached, Exception):
                # A batch-specific inconsistency is not evidence that the
                # original scalar row fails. Let the original gates decide at
                # this exact row, including any real delimiter/length error.
                context.adapter.stats["single_row_fallbacks"] += 1
                return _ORIGINAL_TOKENIZE(row, tokenizer, max_sequence_tokens)
            # Caller owns its result; even accidental edits cannot poison cache.
            return {k: list(v) if isinstance(v, list) else v for k, v in cached.items()}
        context.adapter.stats["single_row_fallbacks"] += 1
    return _ORIGINAL_TOKENIZE(row, tokenizer, max_sequence_tokens)


@contextmanager
def _payload(entry, path):
    # Hash, member, protected-name, gzip/CRC and stream lifetime checks stay
    # entirely inside the original archive payload context manager.
    with _ORIGINAL_PAYLOAD(entry, path) as stream:
        context = getattr(_LOCAL, "context", None)
        if (context is not None and entry["role"] == "candidate_chat"
                and member_key(entry) == context.key):
            yield context.adapter._lines(stream, context)
        else:
            yield stream


class BatchTokenAuditAdapter:
    def __init__(self, tokenizer, batch_size=128, max_rendered_chars=2_000_000,
                 max_raw_chars=2_000_000):
        import transformers
        if transformers.__version__ != "5.16.1":
            raise ValueError("Exact adapter requires transformers 5.16.1")
        revision = tokenizer.init_kwargs.get("_commit_hash")
        if revision != L.REVISION and Path(tokenizer.name_or_path).name != L.REVISION:
            raise ValueError("Pinned Qwen3 tokenizer revision required")
        if not tokenizer.is_fast or tokenizer.convert_tokens_to_ids("<|im_end|>") != 151645:
            raise ValueError("Official fast Qwen3 tokenizer required")
        if batch_size not in (128, 256):
            raise ValueError("batch_size must be 128 or 256")
        if max_rendered_chars <= 0 or max_raw_chars <= 0:
            raise ValueError("Positive character bounds required")
        self.tokenizer = tokenizer
        self.batch_size = batch_size
        self.max_rendered_chars = max_rendered_chars
        self.max_raw_chars = max_raw_chars
        self.stats = dict(batches=0, rows_batched=0, cache_hits=0,
                          single_row_fallbacks=0, skipped_resume_lines=0,
                          max_cache_rows=0, max_rendered_chars=0, max_raw_chars=0,
                          batch_prepare_fallbacks=0, row_prepare_fallbacks=0,
                          cache_key_fallbacks=0, stream_error_buffered_rows=0)

    def install(self):
        global _OWNER
        with _LOCK:
            if _OWNER is not None:
                raise RuntimeError("An adapter is already installed")
            if L.tokenize_assistant_only is not _ORIGINAL_TOKENIZE or A.payload is not _ORIGINAL_PAYLOAD:
                raise RuntimeError("Original tokenizer/payload hooks changed; refuse replacement")
            L.tokenize_assistant_only, A.payload = _tokenize, _payload
            _OWNER = self
        return self

    def uninstall(self):
        global _OWNER
        with _LOCK:
            if _OWNER is not self:
                raise RuntimeError("This adapter is not installed")
            if _ACTIVE:
                raise RuntimeError("Wait for every adapter consume to finish before uninstall")
            if L.tokenize_assistant_only is not _tokenize or A.payload is not _payload:
                raise RuntimeError("Installed hooks changed; refuse to overwrite")
            L.tokenize_assistant_only, A.payload = _ORIGINAL_TOKENIZE, _ORIGINAL_PAYLOAD
            _OWNER = None

    @contextmanager
    def installed(self):
        self.install()
        try:
            yield self
        finally:
            self.uninstall()

    def consume(self, audit, entry, path, max_rows=20000, commit_every=256):
        global _ACTIVE
        with _LOCK:
            if _OWNER is not self:
                raise RuntimeError("Explicitly install adapter before consume")
            if getattr(_LOCAL, "context", None) is not None:
                raise RuntimeError("Nested adapter consume is unsupported")
            if audit.tokenizer is not self.tokenizer:
                raise ValueError("Audit tokenizer must be the exact adapter tokenizer instance")
            cursor = audit.db.execute("SELECT next_line FROM members WHERE id=?",
                                      (member_key(entry),)).fetchone()
            context = _Context(self, audit, member_key(entry), cursor[0] if cursor else 0, max_rows)
            _LOCAL.context = context
            _ACTIVE += 1
        try:
            # All source/hash/split/linkage/duplicate/commit/cursor logic is the
            # actual original scanner method, including its original exceptions.
            return audit.consume(entry, path, max_rows, commit_every)
        finally:
            context.cache.clear()
            with _LOCK:
                del _LOCAL.context
                _ACTIVE -= 1

    def _item(self, text):
        # Invalid syntax/schema is left untouched for the original line reader
        # and original _chat validation, preserving their error order.
        if len(text) > self.max_raw_chars:
            return None
        try:
            row = json.loads(text)
            if not isinstance(row, dict):
                return None
            L.validate_chat(row)
        except (ValueError, TypeError, KeyError, AttributeError):
            return None
        prefix = self.tokenizer.apply_chat_template(row["messages"][:2], tokenize=False,
                    add_generation_prompt=True, enable_thinking=False)
        rendered = self.tokenizer.apply_chat_template(row["messages"], tokenize=False,
                    add_generation_prompt=False, enable_thinking=False)
        if len(prefix) + len(rendered) > self.max_rendered_chars:
            return None
        return (text, row, _row_bytes(row), prefix, rendered)

    def _prepare(self, items, context):
        context.cache.clear()
        if not items:
            return
        # Two independent actual fast-tokenizer batch calls: official template
        # IDs versus rendered text + character offsets. No padding/truncation.
        full = self.tokenizer.apply_chat_template([x[1]["messages"] for x in items],
                    tokenize=True, add_generation_prompt=False, enable_thinking=False)
        ids = full["input_ids"] if hasattr(full, "keys") else full
        offsets = self.tokenizer([x[4] for x in items], add_special_tokens=False,
                    return_offsets_mapping=True, padding=False, truncation=False)
        if len(ids) != len(items) or len(offsets["input_ids"]) != len(items):
            raise ValueError("Official tokenizer batch cardinality differs")
        for index, item in enumerate(items):
            prepared = _PreparedTokenizer(item, ids[index],
                {"input_ids": offsets["input_ids"][index],
                 "offset_mapping": offsets["offset_mapping"][index]})
            try:
                encoded = _ORIGINAL_TOKENIZE(item[1], prepared, context.audit.limit)
            except (ValueError, AssertionError) as error:
                # Defer the exact original gate failure until _chat reaches
                # this row; prior rows keep their original commit behavior.
                encoded = error.with_traceback(None)
            context.cache[item[2]] = encoded
        self.stats["batches"] += 1
        self.stats["rows_batched"] += len(items)
        self.stats["max_cache_rows"] = max(self.stats["max_cache_rows"], len(context.cache))
        self.stats["max_rendered_chars"] = max(self.stats["max_rendered_chars"],
                                                 sum(len(x[3]) + len(x[4]) for x in items))
        self.stats["max_raw_chars"] = max(self.stats["max_raw_chars"], sum(len(x[0]) for x in items))

    def _lines(self, stream, context):
        batch, raw_chars, rendered_chars = [], 0, 0

        def flush(prepare=True):
            context.cache.clear()
            if prepare:
                try:
                    self._prepare(batch, context)
                except Exception:
                    # A batch-only backend/cardinality/index failure must not
                    # move a row's original error/commit boundary. Discard even
                    # a partially prepared cache and run every original row.
                    context.cache.clear()
                    self.stats["batch_prepare_fallbacks"] += 1
            for item in batch:
                yield item[0]
            context.cache.clear()

        try:
            iterator, number = iter(stream), 0
            while True:
                try:
                    text = next(iterator)
                except StopIteration:
                    if batch:
                        yield from flush()
                    break
                except Exception:
                    # Reading ahead can hit Unicode/CRC/trailer/I/O failures.
                    # Deliver every previously read physical row via the exact
                    # original path before surfacing this stream exception.
                    self.stats["stream_error_buffered_rows"] += len(batch)
                    yield from flush(prepare=False)
                    raise
                number += 1
                if number <= context.start:
                    self.stats["skipped_resume_lines"] += 1
                    yield text  # Original enumerate/skip retains physical cursor.
                    continue
                if context.max_rows is not None and number > context.start + context.max_rows:
                    raise AssertionError("Original consume read beyond its own work bound")
                try:
                    item = self._item(text)
                except Exception:
                    # Rendering/canonicalization ahead of _chat is speculative;
                    # fallback preserves duplicate short-circuits and lets the
                    # real original call raise only at its physical row.
                    self.stats["row_prepare_fallbacks"] += 1
                    item = None
                size = len(item[3]) + len(item[4]) if item else 0
                if (batch and (item is None or len(batch) >= self.batch_size
                              or raw_chars + len(text) > self.max_raw_chars
                              or rendered_chars + size > self.max_rendered_chars)):
                    yield from flush()
                    batch, raw_chars, rendered_chars = [], 0, 0
                if item is None:
                    yield text  # Exact original fallback; never drop a line.
                else:
                    batch.append(item)
                    raw_chars += len(text)
                    rendered_chars += size
                if (len(batch) == self.batch_size or
                        context.max_rows is not None and number == context.start + context.max_rows):
                    yield from flush()
                    batch, raw_chars, rendered_chars = [], 0, 0
        finally:
            context.cache.clear()
