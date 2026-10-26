"""Derived conditional tutor prompt. Frozen sources/targets are never rewritten."""
from __future__ import annotations
import hashlib,importlib.util,json
from pathlib import Path

HERE=Path(__file__).resolve().parent
LOCAL=HERE/'behavior_renderer.py'
BASE_PATH=LOCAL if LOCAL.is_file() else HERE.parent/'skill_recovery_150m_20261024/behavior_renderer.py'
BASE_SHA='763da2f7a1931962a9ad1a49b16d4b8dfe5263a09e69603c49959adb02a5ec8f'
if hashlib.sha256(BASE_PATH.read_bytes()).hexdigest()!=BASE_SHA:
    raise ValueError('Frozen behavior renderer differs; do not silently migrate')
spec=importlib.util.spec_from_file_location('conditional_grounding_frozen_renderer',BASE_PATH)
BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)
VERSION='conditional_behavior_render.v1'
SYSTEM=BASE.SYSTEM
WORKED_INSTRUCTION=(
 'Trước hết kiểm tra dữ kiện và yêu cầu của đề. '
 'Nếu dữ kiện đủ và nhất quán, giải từng bước, giải thích vì sao dùng phép tính hoặc quan hệ đó, '
 'giữ đúng ý nghĩa từng số và đơn vị; kiểm lại kết quả. '
 'Nếu đề thiếu dữ kiện hoặc có dữ kiện mâu thuẫn, chỉ rõ phần thiếu hoặc mâu thuẫn và hỏi nguồn cần bổ sung hay kiểm lại; '
 'không tự chọn số liệu, số đo hoặc tự nhận đã nhìn ảnh hay đo được. '
 'Nếu có lời làm của học sinh, chỉ kiểm đúng những dòng đã được cung cấp, nêu chỗ đúng và chỗ cần sửa nếu có; '
 'không đoán thêm thao tác hoặc suy nghĩ chưa được cho.'
)

def prompt(value):
    original=BASE.prompt(value)
    if value['mode']!='worked_solution':
        return original
    suffix='\n\nYêu cầu:\n\n'+BASE._MODE_INSTRUCTIONS['worked_solution']
    if not original.endswith(suffix):
        raise ValueError('Frozen trailing instruction mismatch')
    return original[:-len(suffix)]+'\n\nYêu cầu:\n\n'+WORKED_INSTRUCTION

def render(row):
    projected,proof=BASE.render(row)
    source_prompt=json.loads(row['messages'][1]['content'])
    previous=projected['messages'][1]['content']
    projected['messages'][1]['content']=prompt(source_prompt)
    proof={**proof,'renderer_version':VERSION,'frozen_base_renderer_sha256':BASE_SHA,
           'previous_derived_prompt_sha256':hashlib.sha256(previous.encode()).hexdigest(),
           'derived_prompt_sha256':hashlib.sha256(projected['messages'][1]['content'].encode()).hexdigest(),
           'changed_only_conditional_worked_instruction':row['mode']=='worked_solution',
           'target_unchanged_from_frozen_behavior_renderer':True,
           'new_human_review_or_credential_claimed':False}
    return projected,proof
