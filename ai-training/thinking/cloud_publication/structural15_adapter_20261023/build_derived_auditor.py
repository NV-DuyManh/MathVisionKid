"""Create the Structural15-derived auditor from the frozen v3 source bytes."""
from pathlib import Path
import argparse
import hashlib

ROOT = Path(__file__).resolve().parents[3]
PARENT = ROOT / "thinking" / "math_data_full_audit_v3.py"
PARENT_SHA256 = "02431da433060a6574127f9a8e14d90cabffe85d8d0150c3b2a331dc15b4be1f"
HERE = Path(__file__).resolve().parent
ADAPTER = HERE / "exact_structural15_adapter.py"
BINDINGS = HERE / "bindings.json"


def derive(destination):
    parent = PARENT.read_bytes()
    parent_sha = hashlib.sha256(parent).hexdigest()
    if parent_sha != PARENT_SHA256:
        raise ValueError("Frozen v3 auditor hash differs; refusing derivation")
    adapter_sha = hashlib.sha256(ADAPTER.read_bytes()).hexdigest()
    bindings_sha = hashlib.sha256(BINDINGS.read_bytes()).hexdigest()
    if bindings_sha != "95d9fbf8536b908a6456256d8ff04175e8bd017cd34a406e190513844d316e87":
        raise ValueError("Structural15 bindings hash differs")
    text = parent.decode("utf-8").replace("\r\n", "\n")

    def replace_once(old, new):
        nonlocal text
        if text.count(old) != 1:
            raise ValueError("Expected exactly one frozen replacement site: " + old[:80])
        text = text.replace(old, new, 1)

    replace_once("import math_data_primary782_bindings_v3 as PRIMARY\n\n", "import math_data_primary782_bindings_v3 as PRIMARY\nimport exact_structural15_adapter as STRUCTURAL\n\n")
    replace_once("PRIMARY_ADAPTER_KIND='EXACT_PRIMARY782_NEUTRAL_EXPORT_V3'\n", "PRIMARY_ADAPTER_KIND='EXACT_PRIMARY782_NEUTRAL_EXPORT_V3'\nSTRUCTURAL_ADAPTER_CODE_SHA256='" + adapter_sha + "'\nSTRUCTURAL_BINDINGS_SHA256='" + bindings_sha + "'\nSTRUCTURAL_ADAPTER_KIND=STRUCTURAL.ADAPTER_KIND\n")
    replace_once("def plan_identity(recipe):\n", "def verify_structural_bindings():\n    if hashlib.sha256(Path(STRUCTURAL.__file__).read_bytes()).hexdigest()!=STRUCTURAL_ADAPTER_CODE_SHA256:\n        raise ValueError('Structural15 adapter code hash differs')\n    if hashlib.sha256(STRUCTURAL.BINDINGS_PATH.read_bytes()).hexdigest()!=STRUCTURAL_BINDINGS_SHA256:\n        raise ValueError('Structural15 binding file hash differs')\n\ndef plan_identity(recipe):\n    verify_structural_bindings()\n")
    replace_once("        verify_primary_bindings()\n", "        verify_primary_bindings()\n        verify_structural_bindings()\n")
    replace_once("primary782_adapter_code_sha256=PRIMARY_BINDINGS_CODE_SHA256))", "primary782_adapter_code_sha256=PRIMARY_BINDINGS_CODE_SHA256,structural15_adapter_code_sha256=STRUCTURAL_ADAPTER_CODE_SHA256,structural15_bindings_sha256=STRUCTURAL_BINDINGS_SHA256))")
    replace_once("            if key in self.primary_source_keys:\n", "            if row.get('sample_id') in STRUCTURAL.BINDINGS:\n                projection,binding=STRUCTURAL.binding_source(row,h)\n                original_sha=binding['source_canonical_sha256'];kind=STRUCTURAL_ADAPTER_KIND\n                verification_digest=binding['verification_digest']\n            elif key in self.primary_source_keys:\n")
    replace_once("        L.validate_chat(row);sid=L.case_id(row);h=digest(row)\n", "        sid=L.case_id(row);h=digest(row)\n        L.validate_chat(row)\n        if sid in STRUCTURAL.BINDINGS:\n            STRUCTURAL.validate_chat(row,rawhash(text))\n")
    replace_once("            if source[5]==PRIMARY_ADAPTER_KIND:\n", "            if source[5]==STRUCTURAL_ADAPTER_KIND:\n                return (original==source[4] and row.get('row_sha256')==source[6]\n                        and digest(row.get('verification'))==source[7])\n            if source[5]==PRIMARY_ADAPTER_KIND:\n")
    replace_once("origin=('PRIMARY_ORIGINAL_AND_EXPORTED_HASH_VERIFIED' if source[5]==PRIMARY_ADAPTER_KIND else 'ORIGINAL_RAW_HASH_VERIFIED' if original else 'READ_TIME_DERIVED_BY_FULL_PROMPT_TARGET_LINKAGE')", "origin=('STRUCTURAL15_RAW_CANONICAL_AND_CHAT_HASH_VERIFIED' if source[5]==STRUCTURAL_ADAPTER_KIND else 'PRIMARY_ORIGINAL_AND_EXPORTED_HASH_VERIFIED' if source[5]==PRIMARY_ADAPTER_KIND else 'ORIGINAL_RAW_HASH_VERIFIED' if original else 'READ_TIME_DERIVED_BY_FULL_PROMPT_TARGET_LINKAGE')")
    replace_once("    'original_source_and_exported_row_hashes_distinct':True,\n", "    'original_source_and_exported_row_hashes_distinct':True,\n    'structural15_exact_adapter_code_sha256':'" + adapter_sha + "',\n    'structural15_bindings_sha256':'" + bindings_sha + "',\n    'frozen_v3_parent_sha256':'" + PARENT_SHA256 + "',\n")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8", newline="")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    derive(parser.parse_args().destination)
