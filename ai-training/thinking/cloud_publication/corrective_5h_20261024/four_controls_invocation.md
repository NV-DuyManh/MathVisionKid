The code is prepared locally; no Drive or Colab calls were executed by its author.
Stage `prepare_four_controls_runtime.py` and `four_controls_transaction.py` inside
`root5`. The only required existing notebook globals are `root5` (a Path) and
`repair_credentials`. The controller must additionally supply:

- `canonical_context_bytes`: exact UTF-8 bytes from the root-owned canonical file.
  They must extend the freshly downloaded context's full byte prefix. A mismatch
  fails before publication; reconcile the canonical history explicitly.
- `actual_worker_observation`: fresh process evidence, with `observed_utc` and an
  actual boolean `worker_alive`; include PID/exit status if available. Do not use
  a fixed `True`. Training status is copied from captured training/progress.json.
- `evidence_paths`: an explicit mapping of relative archive names to small code
  or JSON/Markdown/text metadata paths. No recursive scan, corpus, model files,
  generation directories, ZIP checkpoints or JSONL payloads are accepted.

After reviewing the staged bytes, run explicitly in the notebook/controller:

```python
import importlib.util, sys
from datetime import datetime, timezone

def import_control_module(name):
    spec = importlib.util.spec_from_file_location(name, root5 / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

prepare = import_control_module('prepare_four_controls_runtime')
transaction = import_control_module('four_controls_transaction')
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
work = root5 / 'four_controls_publication' / stamp

# Dedicated new authenticated HTTP clients; rate-limited separately from the
# ongoing artifact publisher. These calls read the four existing controls only.
parents = transaction.download_current_parents_with_credentials(
    repair_credentials, prepare.IDS, work / 'parents', min_request_interval=0.5)

# Captures only explicit small metadata snapshots; no training or API writes.
observation = prepare.capture_branch_metadata(
    root5, worker_observation=actual_worker_observation)
prepared = prepare.prepare_controls(
    parents, canonical_context_bytes, observation, evidence_paths,
    work / 'prepared')

# Review prepared_control_updates.json and next_* bytes before this call.
receipt = transaction.publish_with_credentials(
    repair_credentials, prepared['parents'], prepared['controls'], work,
    receipt_path=work / 'four_controls_raw_verified.json',
    min_request_interval=0.5)
assert [x['kind'] for x in receipt['verified_writes']] == [
    'progress', 'chat', 'context', 'state']
assert all(x['fresh_raw_readback_verified'] for x in receipt['verified_writes'])
```

Keep the canonical context's preparation separate from publication. All legacy
state/chat fields and accepted-case/chat counters are preserved. Actual worker,
training and publication observations live in `latest_corrective5h_branch`;
earlier corrective branch snapshots are retained in history. Receipts do not
claim that training is globally disabled. They certify only control-byte integrity.

The transaction guards all four remote parent hashes before its first write,
checks each remote again immediately before updating, writes state last and
performs a fresh raw-media download/hash after each control. On interruption,
retry the same prepared paths and receipt; exact already-published bytes are
verified and reused. A new later/completed observation requires fresh parents and
a fresh staging directory. Concurrent control changes stop the transaction;
there is no automatic rollback or overwrite of unrelated newer bytes.
