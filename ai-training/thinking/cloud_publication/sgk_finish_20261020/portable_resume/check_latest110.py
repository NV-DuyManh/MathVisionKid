"""Bounded real-tokenizer check of already accepted110 only. No training."""
from pathlib import Path
import json
import sys
import time

OUT = Path(__file__).resolve().parent
THINKING = OUT.parents[2]
sys.path.insert(0, str(THINKING))
import exhaustive_colab_loader as L
import math_data_archive_audit as A
import math_data_portable_resume as P


def main():
    catalog = json.loads((OUT / "member_catalog.json").read_text("utf-8"))
    checkpoint = json.loads((OUT / "portable_checkpoint.json").read_text("utf-8"))
    old = THINKING / "cloud_publication/sgk_page_audit_20261019"
    archive = Path(json.loads((old / "bundle_local.json").read_text("utf-8"))["path"])
    local = Path.home() / ".cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots" / L.REVISION
    tokenizer = L.load_qwen_tokenizer(local)
    selected = [(i,entry) for i,entry in enumerate(catalog["members"]) if entry["family"] == "sgk_page_audit_20261019" and entry["role"] in ("candidate_source","candidate_chat")]
    selected.sort(key=lambda pair: pair[1]["role"] != "candidate_source")
    events = []
    for index, entry in selected:
        task = next(k for k,v in checkpoint["tasks"].items() if v.get("catalog_entry") == index)
        token = P.claim(checkpoint, task, "portable-data-worker", ttl=3600)
        if token is None:
            continue
        store = A.AuditStore(OUT / "latest110_audit.sqlite", catalog, tokenizer)
        try:
            first = store.consume(entry, archive, max_rows=128 if entry["role"] == "candidate_chat" else None)
            report = store.report()
        finally:
            store.close()
        P.acknowledge(checkpoint, task, token, {"sqlite_file":"latest110_audit.sqlite", "next_unconsumed_line":first["rows"], "role":entry["role"]})
        P.save(OUT / "portable_checkpoint.json", checkpoint)
        events.append({"entry":index, "first":first, "after_first":report})
        if not first.get("complete"):
            # Reopen SQLite and iterator to emulate a fresh process/account.
            store = A.AuditStore(OUT / "latest110_audit.sqlite", catalog, tokenizer)
            try:
                last = store.consume(entry, archive)
                report = store.report()
            finally:
                store.close()
            events[-1].update(resumed=last, after_resume=report)
        P.acknowledge(checkpoint, task, token, result={"artifact_sha256":entry["sha256"],
            "member_sha256":entry["member_sha256"], "rows":entry["rows"],
            "role":entry["role"], "scope":"ALREADY_ACCEPTED_110_ONLY", "status":"COMPLETE", "training_started":False})
        P.save(OUT / "portable_checkpoint.json", checkpoint)
    store = A.AuditStore(OUT / "latest110_audit.sqlite", catalog, tokenizer)
    try:
        report = store.report()
    finally:
        store.close()
    if report["rows_processed"] != 440 or report["issues"] or report["source_linkage_unverified_rows"] or report["source_raw_row_hash_unverified_rows"] or report["untokenized_rows"]:
        raise ValueError("latest110 bounded audit did not pass: " + json.dumps(report))
    P.save(OUT / "latest110_audit_receipt.json", {"events":events,"final":report,
        "archive_sha256":P.file_hash(archive),"tokenizer_model":L.MODEL,"tokenizer_revision":L.REVISION,
        "data_only":True,"reopened_sqlite_cursor_test":True,"no_weights_loaded":True,
        "all_archived_6501044_chat_audited":False})
    print(json.dumps(report))


if __name__ == "__main__":
    main()
