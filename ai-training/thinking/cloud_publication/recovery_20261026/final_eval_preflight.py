"""Static/import and fake-export checks; never reads sealed fixtures or runs inference."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
path=HERE/"final_eval_worker_20261026.py"
spec=importlib.util.spec_from_file_location("final_eval_worker_20261026",path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assert module.HARD_STOP_UTC=="2026-10-26T11:14:18+00:00"
assert module.MAX_EVALUATION_SECONDS==600
assert module.LOCKED_SHA256=="0526ec69b5b1730376835c2961d32c79c187f6d1d0fe3057f2d98358b71674f7"
assert set(module.CODE_PINS)=={"recovery_worker_20261026.py","native_backend_20261026.py","recovery_policy_20261026.py","inference_contract.py","conditional_behavior_renderer.py","frozen_training_primitives.py"}
assert module.CODE_PINS["recovery_worker_20261026.py"]=="b618f2d961dd0d342f006a8b07abe39268962fc0bdcab43622c425ee2bf67d4f"
assert module.CODE_PINS["native_backend_20261026.py"]=="66aa1473bb6835497fb59b16ab0c76e2a609eec0358d9b7cd03f2662e3f3a046"
assert module.CODE_PINS["recovery_policy_20261026.py"]=="648a6a8f48ded0bf7cb2615451b895e9b3a7d72bfdd294430ec58ce4029384fd"
s=path.read_text(encoding="utf-8")
for stale in ("recovery_worker_v5.py","native_backend_v3.py","recovery_policy_v2.py"):
 assert stale not in s
assert "from native_backend_20261026 import NativeBackend" in s
assert "import recovery_policy_20261026 as policy" in s
assert '"selection_changes_allowed": False' in s

# Check actual export_adapter archive shape: self-manifest is present in the ZIP.
import hashlib,json,tempfile,zipfile
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);generation=root/"generation";generation.mkdir()
 artifact=root/"selected_adapter_export.zip"
 payloads={"adapter_config.json":b"{}\n","adapter_model.safetensors":b"fake-weights","resume_state.pt":b"private-resume"}
 for name,data in payloads.items(): (generation/name).write_bytes(data)
 manifest={"complete":True,"files":{name:hashlib.sha256(data).hexdigest() for name,data in payloads.items()},"file_bytes":{name:len(data) for name,data in payloads.items()}}
 manifest_bytes=(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
 (generation/"generation_manifest.json").write_bytes(manifest_bytes)
 manifest_sha=hashlib.sha256(manifest_bytes).hexdigest()
 with zipfile.ZipFile(artifact,"w",zipfile.ZIP_DEFLATED) as archive:
  for name in ("adapter_config.json","adapter_model.safetensors","generation_manifest.json"): archive.write(generation/name,name)
 module.verify_export_zip(artifact,generation,manifest,manifest_sha)
 tampered=root/"tampered.zip"
 with zipfile.ZipFile(tampered,"w",zipfile.ZIP_DEFLATED) as archive:
  archive.writestr("adapter_config.json",b"tampered")
  archive.writestr("adapter_model.safetensors",payloads["adapter_model.safetensors"])
  archive.writestr("generation_manifest.json",manifest_bytes)
 try: module.verify_export_zip(tampered,generation,manifest,manifest_sha)
 except ValueError: pass
 else: raise AssertionError("tampered archive member was accepted")
 extra=root/"extra.zip"
 with zipfile.ZipFile(extra,"w",zipfile.ZIP_DEFLATED) as archive:
  for name in ("adapter_config.json","adapter_model.safetensors","generation_manifest.json"): archive.write(generation/name,name)
  archive.writestr("unexpected.txt",b"extra")
 try: module.verify_export_zip(extra,generation,manifest,manifest_sha)
 except ValueError: pass
 else: raise AssertionError("unexpected archive member was accepted")
print("PASS: evaluator imports/bindings and actual self-manifest ZIP verification; tamper/extra rejected")

