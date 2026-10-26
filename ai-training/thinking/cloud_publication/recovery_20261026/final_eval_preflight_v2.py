"""Static/import-only checks for v2 precision-matched evaluator; no GPU/data access."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
path=HERE/"final_eval_worker_20261026_v2.py"
spec=importlib.util.spec_from_file_location("final_eval_worker_20261026_v2",path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
s=path.read_text(encoding="utf-8")
assert module.HARD_STOP_UTC=="2026-10-26T11:14:18+00:00"
assert module.MAX_EVALUATION_SECONDS==600
assert module.CODE_PINS["recovery_worker_20261026.py"]=="b618f2d961dd0d342f006a8b07abe39268962fc0bdcab43622c425ee2bf67d4f"
base=s.index('generate_fixtures(model, tokenizer, fixtures, final, "base_before_training"')
prepare=s.index('prepare_model_for_kbit_training(model,use_gradient_checkpointing=False)')
attach=s.index('PeftModel.from_pretrained(model, str(generation), is_trainable=False)')
assert base < prepare < attach
assert 'final_eval_20261026_v2' in s
assert 'nonquant_parameter_dtypes_before' in s and 'nonquant_parameter_dtypes_after' in s
assert 'Loaded PEFT config differs from selected checkpoint config' in s
assert 'get_peft_model_state_dict' in s and 'torch.equal' in s
assert 'candidate_precision_preparation.json' in s
assert 'from native_backend_20261026 import NativeBackend' in s
print("PASS: v2 import, training-order precision preparation, selected-config and adapter checks, separate output path")
