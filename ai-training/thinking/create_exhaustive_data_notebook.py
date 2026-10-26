"""Write a small data-only Colab entry point; no trainer or GPU code."""
import json
from pathlib import Path


def cell(source, kind="code"):
    result = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        result.update(execution_count=None, outputs=[])
    return result


def create(path):
    cells = [cell("# MathVisionKid: data-only streaming and token audit\n"
                  "Use the selected balanced manifest. The old chat control ID is a JSON manifest, not JSONL. "
                  "No model weights, training, optimizer or GPU is loaded. Mount the existing Drive folder.\n", "markdown"),
             cell('''from google.colab import drive
drive.mount('/content/drive')
from pathlib import Path
import json, sys
ROOT = Path('/content/drive/MyDrive/MathVisionKid')  # Set to your existing Drive folder.
sys.path.insert(0, str(ROOT / 'thinking'))
from exhaustive_colab_loader import (ManifestStream, load_qwen_tokenizer,
    full_token_audit, tokenized_stream, save_json, asdict)
'''), cell('''manifest = json.loads((ROOT / 'MathVisionKid_BALANCED_TRAINING_MANIFEST.json').read_text())
stream = ManifestStream(manifest, ROOT)
tokenizer = load_qwen_tokenizer()  # Official pinned tokenizer, no model weights.
receipt = full_token_audit(stream, tokenizer)
print({k: v for k, v in receipt.items() if not k.endswith('histogram')})
'''), cell('''# Smoke-read one item. Acknowledge only after successful consumption.
cursor_path = ROOT / 'loader_consumer_cursor.json'
cursor = json.loads(cursor_path.read_text()) if cursor_path.exists() else None
iterator = tokenized_stream(stream, tokenizer, cursor)
item, next_cursor = next(iterator)
print(item['sample_id'], len(item['input_ids']))
# save_json(cursor_path, asdict(next_cursor))
iterator.close()
# No training is invoked. GZIP resume replays only the current shard.
''')]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"cells": cells, "metadata": {"kernelspec": {
        "display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4, "nbformat_minor": 5}, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    print(create(Path(__file__).parent / "cloud_publication/resume_20261018/MathVisionKid_DATA_ONLY_COLAB.ipynb"))
