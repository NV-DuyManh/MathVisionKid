"""Candidate input contract only; importing never loads a model or starts training.

Uses the same pinned base, request modes, seed policy and decoding as the frozen
development contract. No expected answer or source target is used for routing.
Any model trial must be explicitly launched in Colab and its results assessed.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import conditional_behavior_renderer as R

MODEL = 'Qwen/Qwen3-1.7B'
REVISION = '70d244cc86ccca08cf5af4e1e306ecf908b1ad5e'
VERSION = 'MathVisionKid.conditional_inference.v1'
MODE_MAP = {'answer': 'worked_solution', 'hint_no_answer': 'hint_level_1',
            'student_error': 'worked_solution',
            'missing_or_contradictory_info': 'worked_solution'}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def messages(fixture):
    # Only actual user inputs and requested mode enter the prompt. Test-only
    # rubric/oracle fields remain outside the model input.
    request = {'grade': fixture['grade'], 'problem': fixture['userproblem'],
               'mode': MODE_MAP[fixture['mode']]}
    return [{'role': 'system', 'content': R.SYSTEM},
            {'role': 'user', 'content': R.prompt(request)}]


def seed_for(fixture_id):
    return (20261024 + int(sha(fixture_id.encode())[:8], 16)) % (2**31)


def decoding(pad_token_id):
    return {'do_sample': True, 'temperature': .7, 'top_p': .8,
            'top_k': 20, 'min_p': 0., 'num_beams': 1,
            'max_new_tokens': 1024, 'repetition_penalty': 1.,
            'use_cache': True, 'pad_token_id': pad_token_id,
            'eos_token_id': 151645}


def build_contract(fixtures, tokenizer, fixture_raw_sha256):
    if (len(fixture_raw_sha256) != 64 or
            any(c not in '0123456789abcdef' for c in fixture_raw_sha256)):
        raise ValueError('Raw fixture SHA256 required')
    ids = [f['id'] for f in fixtures]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError('Nonempty unique fixture IDs required')
    token_hashes = {}
    for fixture in fixtures:
        tokens = tokenizer.apply_chat_template(
            messages(fixture), tokenize=True, add_generation_prompt=True,
            enable_thinking=False)
        if hasattr(tokens, 'keys'):
            tokens = tokens['input_ids']
        token_hashes[fixture['id']] = sha(canonical(tokens).encode())
    contract = {'schema': VERSION, 'model': MODEL, 'revision': REVISION,
                'fixture_sha256': fixture_raw_sha256, 'fixture_ids': ids,
                'renderer_version': R.VERSION,
                'renderer_sha256': sha(Path(R.__file__).read_bytes()),
                'frozen_base_renderer_sha256': R.BASE_SHA,
                'system_sha256': sha(R.SYSTEM.encode()),
                'prompt_token_sha256': token_hashes,
                'enable_thinking': False, 'add_generation_prompt': True,
                'seed_policy': '20261024 + first8hex fixtureID SHA modulo2^31',
                'decoding': decoding(tokenizer.pad_token_id),
                'expected_answer_oracle_used_in_input': False,
                'arithmetic_checker_changes_outputs': False,
                'model_improvement_established': False}
    return contract, sha(canonical(contract).encode())
