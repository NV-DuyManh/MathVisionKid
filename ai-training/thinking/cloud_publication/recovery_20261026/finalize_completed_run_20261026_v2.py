"""Prepare final assessment and an evidence-bound publisher finalization request.

CPU-only. Does not connect to Drive, start the publisher, execute training,
or inspect sealed fixture contents. Existing artifacts are never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def read_json(path: Path):
    return json.loads(path.read_bytes())


def atomic_exclusive(path: Path, raw: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing evidence: {path}")
    temp = path.with_name(path.name + f".{os.getpid()}.pending")
    with temp.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def atomic_json_exclusive(path: Path, value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    atomic_exclusive(path, raw)


def load_local(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load local helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def build_report(root: Path):
    root = root.resolve()
    training = root / "training"
    config = read_json(training / "run_config.json")
    completion = read_json(training / "run_complete.json")
    progress = read_json(training / "progress.json")
    if completion.get("complete") is not True or progress.get("state") != "COMPLETE":
        raise ValueError("Wait for run_complete plus progress state COMPLETE before assessment")
    if completion.get("production_approval") is not False:
        raise ValueError("Completion may not assert production approval")
    builder_path = root / "build_final_assessment_20261026.py"
    builder = load_local(builder_path, "final_assessment_builder_20261026_v2")
    report = builder.build_assessment(root)
    target = training / "final_semantic_assessment.json"
    atomic_json_exclusive(target, report)
    return report, target


def finalize_request(root: Path, readback_path: Path):
    root = root.resolve()
    training = root / "training"
    report_path = training / "final_semantic_assessment.json"
    completion_path = training / "run_complete.json"
    best_path = training / "best.json"
    for path in (report_path, completion_path, best_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required completed-run artifact missing: {path.name}")
    report, completion, best = map(read_json, (report_path, completion_path, best_path))
    if completion.get("complete") is not True or completion.get("best") != best:
        raise ValueError("Run completion and current selected-best pointer disagree")
    if report.get("production_approved") is not False or report.get("human_review_claimed") is not False:
        raise ValueError("Assessment must not claim production or human approval")
    if report.get("selected_artifact", {}).get("kind") != best.get("kind"):
        raise ValueError("Assessment selected-artifact kind differs from best pointer")

    # A publisher-authored raw readback receipt is required for BOTH the exact
    # assessment and the exact selected artifact before the finalize marker.
    proof = read_json(readback_path)
    if proof.get("schema") != "MathVisionKid.publisher_raw_readback_pair.v1":
        raise ValueError("Unsupported publisher readback receipt schema")
    expected = {
        "assessment": {"sha256": sha(report_path), "bytes": report_path.stat().st_size},
    }
    selected = completion.get("selected_artifact", {})
    if selected.get("kind") != best.get("kind"):
        raise ValueError("Selected artifact kind differs from best pointer")
    if selected.get("kind") == "trained_adapter":
        rel = Path(selected.get("path", ""))
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("Unsafe selected adapter export path")
        artifact_path = training / rel
        if (not artifact_path.is_file() or sha(artifact_path) != selected.get("sha256")
                or artifact_path.stat().st_size != selected.get("bytes")):
            raise ValueError("Selected adapter export differs from run completion")
        expected["selected_artifact"] = {"kind": "trained_adapter", "sha256": sha(artifact_path),
            "bytes": artifact_path.stat().st_size, "manifest_sha256": best.get("manifest_sha256"),
            "path": str(rel)}
    elif selected.get("kind") == "untrained_base":
        expected["selected_artifact"] = {"kind": "untrained_base", "sha256": sha(best_path),
            "bytes": best_path.stat().st_size, "validation_output_sha256": best.get("validation_output_sha256"),
            "path": "training/best.json"}
    else:
        raise ValueError("Unknown selected-artifact kind")
    for key in ("assessment", "selected_artifact"):
        observed = proof.get(key)
        if not isinstance(observed, dict) or observed.get("readback_verified") is not True:
            raise ValueError(f"Fresh raw readback proof missing for {key}")
        for field, value in expected[key].items():
            if observed.get(field) != value:
                raise ValueError(f"Raw readback {key}.{field} differs from local completed artifact")
        if (observed.get("readback_sha256") != observed.get("sha256")
                or observed.get("readback_bytes") != observed.get("bytes")):
            raise ValueError(f"Raw readback bytes do not match uploaded bytes for {key}")

    request = {
        "schema": "MathVisionKid.publisher_finalize_request.v2",
        "finalize_requested": True,
        "final_semantic_assessment_sha256": sha(report_path),
        "run_complete_sha256": sha(completion_path),
        "best_pointer_sha256": sha(best_path),
        "selected_artifact_kind": best.get("kind"),
        "selected_artifact_manifest_sha256": best.get("manifest_sha256"),
        "selected_artifact_validation_output_sha256": best.get("validation_output_sha256"),
        "raw_readback_receipt_sha256": sha(readback_path),
        "production_approved": False,
        "human_review_claimed": False,
    }
    target = root / "publication" / "finalize_requested.json"
    atomic_json_exclusive(target, request)
    return request, target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--mode", choices=("assessment", "finalize"), required=True)
    parser.add_argument("--raw-readback", type=Path,
                        help="Publisher-produced report+selected-artifact fresh-readback receipt; required for finalize")
    args = parser.parse_args()
    if args.mode == "assessment":
        report, path = build_report(args.root)
        result = {"assessment_written": str(path), "assessment_sha256": sha(path),
                  "recommendation": report["recommendation"], "production_approved": False,
                  "publisher_finalized": False}
    else:
        if args.raw_readback is None:
            parser.error("--raw-readback is required for finalize mode")
        request, path = finalize_request(args.root, args.raw_readback)
        result = {"finalize_request_written": str(path),
                  "assessment_sha256": request["final_semantic_assessment_sha256"],
                  "raw_readback_receipt_sha256": request["raw_readback_receipt_sha256"],
                  "publisher_finalized": False, "production_approved": False}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
