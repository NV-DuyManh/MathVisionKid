"""Derived one-tokenizer-call batch preparation for the pinned V3 adapter.

This file leaves the audited V3 scanner and existing batch adapter unchanged.
The derived class retains all stream, cache, fallback, and original row gates.
"""
from __future__ import annotations
import hashlib
import inspect
from pathlib import Path
import transformers
import math_data_batch_token_audit as base

TRANSFORMERS_VERSION = transformers.__version__
TOKENIZER_REVISION = base.L.REVISION


def api_provenance(tokenizer):
    # Pin the installed implementation source used by this derived path.
    from transformers import PreTrainedTokenizer
    source_path = Path(inspect.getsourcefile(PreTrainedTokenizer.apply_chat_template))
    source_bytes = source_path.read_bytes()
    method_source = inspect.getsource(PreTrainedTokenizer.apply_chat_template).encode('utf-8')
    return {
        'transformers_version': TRANSFORMERS_VERSION,
        'tokenizer_revision': TOKENIZER_REVISION,
        'tokenizer_fast': bool(tokenizer.is_fast),
        'apply_chat_template_source_file': source_path.name,
        'apply_chat_template_file_sha256': hashlib.sha256(source_bytes).hexdigest(),
        'apply_chat_template_method_sha256': hashlib.sha256(method_source).hexdigest(),
        'method_behavior_basis': 'Pinned local Transformers source renders conversations, then calls self(rendered_chat, add_special_tokens=False, **tokenizer_kwargs); offset mapping is returned in same BatchEncoding.',
    }


def prepare_official_onepass(adapter, items, context, *, verify_batch_render=True):
    context.cache.clear()
    if not items:
        return
    conversations = [item[1]['messages'] for item in items]
    if verify_batch_render:
        # Cheap render-only comparison proves batched Jinja text matches the
        # exact full text used for the stored scalar prefix/full gates.
        rendered = adapter.tokenizer.apply_chat_template(
            conversations, tokenize=False, add_generation_prompt=False,
            enable_thinking=False)
        adapter.stats['onepass_render_verification_calls'] += 1
        if not isinstance(rendered, list) or len(rendered) != len(items):
            raise ValueError('Official batch render cardinality differs')
        if any(text != item[4] for text, item in zip(rendered, items)):
            raise ValueError('Official batch full render differs from checked row rendering')
    # Transformers 5.16.1 passes tokenizer_kwargs through to its one call to
    # self(rendered_chat,...). Keep padding/truncation on this method because
    # they are explicit apply_chat_template parameters.
    encoded_batch = adapter.tokenizer.apply_chat_template(
        conversations, tokenize=True, return_dict=True,
        tokenizer_kwargs={'return_offsets_mapping': True},
        padding=False, truncation=False, add_generation_prompt=False,
        enable_thinking=False)
    adapter.stats['onepass_official_encoding_calls'] += 1
    if not hasattr(encoded_batch, 'keys') or 'input_ids' not in encoded_batch or 'offset_mapping' not in encoded_batch:
        raise ValueError('Official combined encoding lacks ids or offsets')
    ids = encoded_batch['input_ids']
    offsets = encoded_batch['offset_mapping']
    if len(ids) != len(items) or len(offsets) != len(items):
        raise ValueError('Official combined encoding cardinality differs')
    for index, item in enumerate(items):
        prepared = base._PreparedTokenizer(item, ids[index],
            {'input_ids': ids[index], 'offset_mapping': offsets[index]})
        try:
            result = base._ORIGINAL_TOKENIZE(item[1], prepared, context.audit.limit)
        except (ValueError, AssertionError) as error:
            result = error.with_traceback(None)
        context.cache[item[2]] = result
    adapter.stats['batches'] += 1
    adapter.stats['rows_batched'] += len(items)
    adapter.stats['max_cache_rows'] = max(adapter.stats['max_cache_rows'], len(context.cache))
    adapter.stats['max_rendered_chars'] = max(adapter.stats['max_rendered_chars'],
                                               sum(len(x[3]) + len(x[4]) for x in items))
    adapter.stats['max_raw_chars'] = max(adapter.stats['max_raw_chars'],
                                          sum(len(x[0]) for x in items))


class OnePassBatchTokenAuditAdapter(base.BatchTokenAuditAdapter):
    """Same audited row path; combine official IDs and offsets into one call."""
    def __init__(self, tokenizer, **kwargs):
        super().__init__(tokenizer, **kwargs)
        self.stats['onepass_official_encoding_calls'] = 0
        self.stats['onepass_render_verification_calls'] = 0

    def _prepare(self, items, context):
        prepare_official_onepass(self, items, context, verify_batch_render=True)
