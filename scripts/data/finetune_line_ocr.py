"""Bounded CRNN adaptation on reviewed, page-disjoint private line labels.

Reads original bytes through source_storage; never installs or overwrites a model.
This is a small candidate experiment, not a trainer for 2-D math layouts.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import random
import re
import sys
import unicodedata

from PIL import Image, ImageOps
from source_storage import read_source_bytes

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(text):
    return ' '.join(unicodedata.normalize('NFC', text).split())


def distance(left, right):
    previous = list(range(len(right) + 1))
    for i, a in enumerate(left, 1):
        current = [i]
        for j, b in enumerate(right, 1):
            current.append(min(current[-1] + 1, previous[j] + 1,
                               previous[j - 1] + (a != b)))
        previous = current
    return previous[-1]


def critical(text):
    # Keep every digit, decimal separator and operator; do not solve expressions.
    return ''.join(c for c in canonical(text) if c.isdigit() or c in '+-×*/:=,.%²³')


def line_tensor(crop, preserve_aspect_ratio=False):
    """Experimental input policy; production continues using its fixed resize."""
    from app.ocr.crnn_provider import _TRANSFORM, IMG_H, IMG_W
    if not preserve_aspect_ratio:
        return _TRANSFORM(crop)
    # Width is a multiple of the CNN stride. No padding is fed to the BiLSTM.
    width = min(IMG_W, max(64, round(crop.width * IMG_H / crop.height / 8) * 8))
    from torchvision.transforms.functional import resize
    resized = resize(crop, [IMG_H, width])
    return _TRANSFORM.transforms[2](_TRANSFORM.transforms[1](resized))


def metrics(rows, predictions):
    if len(rows) != len(predictions):
        raise ValueError('Every reference must have exactly one prediction')
    references = [canonical(row['text']) for row in rows]
    predictions = [canonical(text) for text in predictions]
    errors = sum(distance(a, b) for a, b in zip(references, predictions))
    chars = sum(map(len, references))
    math_rows = [(critical(a), critical(b)) for a, b in zip(references, predictions)
                 if critical(a)]
    math_errors = sum(distance(a, b) for a, b in math_rows)
    math_chars = sum(len(a) for a, _ in math_rows)
    return {'lines': len(rows), 'character_errors': errors, 'reference_chars': chars,
            'cer': errors / chars if chars else None,
            'exact_lines': sum(a == b for a, b in zip(references, predictions)),
            'critical_lines': len(math_rows), 'critical_errors': math_errors,
            'critical_chars': math_chars,
            'critical_cer': math_errors / math_chars if math_chars else None,
            'critical_exact_lines': sum(a == b for a, b in math_rows)}


def scoped_metrics(rows, predictions):
    if len(rows) != len(predictions):
        raise ValueError('Every scope must have exactly one prediction')
    roles = sorted({row.get('math_role', 'text_line') for row in rows})
    return {role: metrics([row for row in rows if row.get('math_role', 'text_line') == role],
                          [text for row, text in zip(rows, predictions)
                           if row.get('math_role', 'text_line') == role]) for role in roles}


def decode_ctc(sequences, vocabulary):
    inverse = {value: char for char, value in vocabulary.items()}
    decoded = []
    for sequence in sequences:
        previous, chars = None, []
        for value in sequence:
            if value and value != previous:
                chars.append(inverse[value])
            previous = value
        decoded.append(''.join(chars))
    return decoded


def load_reviewed(manifest, data_root):
    """Reject uncertainty, non-line layouts and any page/pixel/line split leakage."""
    document = json.loads(Path(manifest).read_text(encoding='utf-8'))
    rows = document['records']
    if not rows or len(rows) > 512:
        raise ValueError('Use a bounded cohort of 1 to 512 reviewed records')
    seen, groups, hashes, pixels, crops = set(), {}, {}, {}, {}
    sources, result = {}, []
    data_root = Path(data_root).resolve()
    for row in rows:
        ident = row['id']
        if ident in seen:
            raise ValueError('Duplicate record ID')
        seen.add(ident)
        split = row['split']
        if split not in {'TRAIN', 'DEV', 'HOLDOUT'}:
            raise ValueError('Unknown split')
        if (row.get('review_status') != 'verified' or row.get('uncertain') is not False
                or not row.get('reviewer') or not row.get('source_group')):
            raise ValueError('Unreviewed or uncertain label')
        if row.get('layout') != 'TEXT_LINE':
            raise ValueError('2-D math blocks cannot be trained as text lines')
        if split == 'TRAIN' and row.get('training_eligible') is not True:
            raise ValueError('Training requires explicit eligibility')
        text = row['text']
        if not isinstance(text, str) or not canonical(text) or '?' in text or '<blank>' in text:
            raise ValueError('Unread or invalid transcript')
        if len(canonical(text)) > 128:
            raise ValueError('Transcript exceeds CRNN time steps')
        source = row['source']
        folder = (data_root / row['source_batch']).resolve()
        if not folder.is_relative_to(data_root):
            raise ValueError('Source batch must stay inside the dataset')
        key = source['drive_id'], source['sha256'], str(folder)
        if key not in sources:
            raw = read_source_bytes(folder, source)
            if hashlib.sha256(raw).hexdigest() != source['sha256']:
                raise ValueError('Source SHA-256 mismatch')
            sources[key] = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert('RGB')
        image = sources[key]
        box = row['box']
        if (len(box) != 4 or any(type(x) is not int for x in box)
                or not (0 <= box[0] < box[2] <= image.width
                        and 0 <= box[1] < box[3] <= image.height)):
            raise ValueError('Invalid reviewed box')
        crop = image.crop(box)
        page_pixel = hashlib.sha256(str(image.size).encode() + image.tobytes()).hexdigest()
        crop_pixel = hashlib.sha256(str(crop.size).encode() + crop.tobytes()).hexdigest()
        for mapping, identity in ((groups, row['source_group']), (hashes, source['sha256']),
                                  (pixels, page_pixel), (crops, crop_pixel)):
            if mapping.setdefault(identity, split) != split:
                raise ValueError('Source or pixel leakage across splits')
        result.append((row, crop))
    if {row['split'] for row, _ in result} != {'TRAIN', 'DEV', 'HOLDOUT'}:
        raise ValueError('TRAIN, DEV and HOLDOUT must all be present')
    return document, result


def gate(baseline, candidate):
    reasons = []
    for split in ('DEV', 'HOLDOUT'):
        old, new = baseline[split], candidate[split]
        if new['cer'] > old['cer']:
            reasons.append(split + ': character regression')
        if new['critical_errors'] > old['critical_errors']:
            reasons.append(split + ': digit/operator regression')
        if new.get('exact_lines', 0) < old.get('exact_lines', 0):
            reasons.append(split + ': exact-line regression')
    if candidate['HOLDOUT']['cer'] >= baseline['HOLDOUT']['cer']:
        reasons.append('HOLDOUT: no character improvement')
    # Experiment promotion needs stronger evidence than a small same-writer sample.
    if candidate['HOLDOUT']['cer'] > 0.05:
        reasons.append('HOLDOUT: CER exceeds 5%')
    if candidate['HOLDOUT']['critical_errors']:
        reasons.append('HOLDOUT: unresolved digit/operator errors')
    return {'experiment_passed': not reasons, 'reasons': reasons,
            'production_promoted': False,
            'scope': 'page-disjoint for this adaptation; writer independence unknown'}


def run(args):
    trainer_source = Path(__file__).read_bytes()
    manifest_source = args.manifest.read_bytes()
    manifest_sha256 = hashlib.sha256(manifest_source).hexdigest()
    if not (1 <= args.epochs <= 30 and 1 <= args.batch_size <= 16
            and 1 <= args.threads <= 8 and 0 < args.learning_rate <= 0.01):
        raise ValueError('Use bounded epochs, batch size, threads and learning rate')
    output, model_dir = args.output.resolve(), args.model_dir.resolve()
    if (output.is_relative_to((ROOT / 'ai/runtime/models').resolve())
            or output.is_relative_to(model_dir) or model_dir.is_relative_to(output)):
        raise ValueError('Candidate output must not contain or replace production models')
    if output.exists():
        raise ValueError('Use a fresh output directory; previous evidence is immutable')
    document, samples = load_reviewed(args.manifest, args.data_root)
    if json.loads(manifest_source.decode('utf-8')) != document:
        raise ValueError('Reviewed manifest changed while it was being loaded')
    numeric_only = getattr(args, 'numeric_fields_only', False)
    if numeric_only and any(row.get('content_kind') != 'UNSIGNED_NUMERIC_FIELD'
                            or not re.fullmatch(r'[0-9]+(?:[,. ][0-9]+)*', canonical(row['text']))
                            for row, _ in samples):
        raise ValueError('Numeric model requires explicitly reviewed unsigned numeric fields only')
    import torch
    import torch.nn.functional as F
    sys.path.insert(0, str(ROOT / 'ai/runtime'))
    from app.ocr.model import CRNN

    torch.set_num_threads(args.threads)
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    weights, vocab_path = model_dir / 'best_cer.pth', model_dir / 'vocab.json'
    before = {str(path): digest(path) for path in (weights, vocab_path)}
    vocab = json.loads(vocab_path.read_text(encoding='utf-8'))
    if vocab.get('<blank>') != 0 or sorted(vocab.values()) != list(range(len(vocab))):
        raise ValueError('Vocabulary must have contiguous IDs and blank 0')
    original_vocab = vocab.copy()
    original_size = len(vocab)
    # Only TRAIN can define new classes. Held-out text must not change the model.
    new_chars = sorted({c for row, _ in samples if row['split'] == 'TRAIN'
                        for c in canonical(row['text']) if c not in vocab})
    for char in new_chars:
        vocab[char] = len(vocab)
    model = CRNN(original_size)
    model.load_state_dict(torch.load(weights, map_location='cpu', weights_only=True))
    original_head = model.fc
    if numeric_only:
        vocab = {'<blank>': 0, **{char: i for i, char in enumerate('0123456789., ', 1)}}
        new_chars = []
        model.fc = torch.nn.Linear(256, len(vocab))
        with torch.no_grad():
            for char, ident in vocab.items():
                if char not in original_vocab:
                    raise ValueError('Base checkpoint lacks a required numeric field character')
                model.fc.weight[ident].copy_(original_head.weight[original_vocab[char]])
                model.fc.bias[ident].copy_(original_head.bias[original_vocab[char]])
    elif new_chars:
        model.fc = torch.nn.Linear(256, len(vocab))
        with torch.no_grad():
            model.fc.weight.zero_()
            model.fc.bias.fill_(-12)
            model.fc.weight[:original_size].copy_(original_head.weight)
            model.fc.bias[:original_size].copy_(original_head.bias)
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    for parameter in model.fc.parameters():
        parameter.requires_grad_(True)
    train_visual = getattr(args, 'train_last_visual_block', False)
    train_recurrent = getattr(args, 'train_recurrent', False) or train_visual
    if train_recurrent:
        for parameter in model.rnn.parameters():
            parameter.requires_grad_(True)
    if train_visual:
        for parameter in model.cnn[12:].parameters():
            parameter.requires_grad_(True)
    model.eval()
    features, original_features, rows = [], [], []
    preserve_aspect_ratio = getattr(args, 'preserve_aspect_ratio', False)
    defer_holdout = getattr(args, 'defer_holdout', False)
    evaluated_splits = ('TRAIN', 'DEV') if defer_holdout else ('TRAIN', 'DEV', 'HOLDOUT')
    augment_contrast = getattr(args, 'augment_train_contrast', False)
    views = [(row, crop, False) for row, crop in samples if row['split'] in evaluated_splits]
    if augment_contrast:
        views += [(row, ImageOps.autocontrast(ImageOps.grayscale(crop)).convert('RGB'), True)
                  for row, crop in samples if row['split'] == 'TRAIN']
    if len(views) > 512:
        raise ValueError('Bounded feature cache supports at most 512 original and augmented views')
    original_view = []

    def extract(crop, preserve, visual=False):
        input_tensor = line_tensor(crop, preserve).unsqueeze(0)
        if visual:
            return model.cnn[:12](input_tensor).squeeze(0)
        feat = model.cnn(input_tensor)
        b, c, h, w = feat.shape
        feat = feat.permute(0, 3, 1, 2).contiguous().view(b, w, c * h)
        return feat.squeeze(0) if train_recurrent else model.rnn(feat)[0].squeeze(0)

    # ponytail: bounded reviewed cohort cached in RAM; use a DataLoader for a large cohort.
    with torch.no_grad():
        for i, (row, crop, augmented) in enumerate(views):
            features.append(extract(crop, preserve_aspect_ratio, train_visual))
            original_features.append(extract(crop, False) if preserve_aspect_ratio or train_visual else features[-1])
            rows.append(row)
            original_view.append(not augmented)
            if (i + 1) % 10 == 0:
                print(f'Hash-checked feature extraction: {i + 1}/{len(samples)}', flush=True)
    lengths = [feat.shape[-1] if train_visual else len(feat) for feat in features]
    original_lengths = [len(feat) for feat in original_features]
    if not train_visual:
        features = torch.nn.utils.rnn.pad_sequence(features, batch_first=True)
    original_features = torch.stack(original_features)
    indices = {split: [i for i, row in enumerate(rows) if row['split'] == split]
               for split in evaluated_splits}
    evaluation_indices = {split: [i for i in ids if original_view[i]] for split, ids in indices.items()}
    inv = {value: char for char, value in vocab.items()}

    def logits_for(chosen, source_features=features, source_lengths=lengths, head=None):
        if train_visual and source_features is features:
            sequences = []
            for index in chosen:
                # GroupNorm sees only this crop, never another sample's padding.
                activation = model.cnn[12:](features[index].unsqueeze(0))
                b, c, h, w = activation.shape
                sequences.append(activation.permute(0, 3, 1, 2).reshape(b, w, c*h).squeeze(0))
            feat = torch.nn.utils.rnn.pad_sequence(sequences, batch_first=True)
        else:
            feat = source_features[chosen]
        if train_recurrent:
            # Padding must not become visual context for the backward LSTM.
            packed = torch.nn.utils.rnn.pack_padded_sequence(
                feat, [source_lengths[i] for i in chosen], batch_first=True, enforce_sorted=False)
            recurrent, _ = model.rnn(packed)
            feat, _ = torch.nn.utils.rnn.pad_packed_sequence(recurrent, batch_first=True)
        return (head if head is not None else model.fc)(feat)

    def predict(chosen, source_features=features, source_lengths=lengths, head=None, inverse=None):
        with torch.no_grad():
            sequences = logits_for(chosen, source_features, source_lengths, head).argmax(-1).tolist()
        dictionary = inverse if inverse is not None else inv
        decoded = []
        for index, sequence in zip(chosen, sequences):
            previous, chars = None, []
            for value in sequence[:source_lengths[index]]:
                if value != 0 and value != previous:
                    chars.append(dictionary[value])
                previous = value
            decoded.append(''.join(chars))
        return decoded

    # Compare with unchanged production preprocessing, not the experimental policy.
    baseline_predictions = {s: predict(ids, original_features, original_lengths, original_head,
                                      {value: char for char, value in original_vocab.items()})
                            for s, ids in evaluation_indices.items()}
    baseline = {s: metrics([rows[i] for i in ids], baseline_predictions[s])
                for s, ids in evaluation_indices.items()}
    targets = {}
    for i in indices['TRAIN']:
        text = canonical(rows[i]['text'])
        values = [vocab[c] for c in text]
        required = len(values) + sum(a == b for a, b in zip(values, values[1:]))
        if required > lengths[i]:
            raise ValueError('Repeated characters exceed CTC alignment capacity')
        targets[i] = torch.tensor(values, dtype=torch.long)
    trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
    optimizer = torch.optim.Adam(trainable, lr=args.learning_rate)
    loss_fn = torch.nn.CTCLoss(blank=0, zero_infinity=False)
    best_state, best_epoch = None, None
    best_key, history = (float('inf'), float('inf')), []
    for epoch in range(1, args.epochs + 1):
        chosen = indices['TRAIN'].copy()
        random.shuffle(chosen)
        losses = []
        for start in range(0, len(chosen), args.batch_size):
            batch = chosen[start:start + args.batch_size]
            logits = logits_for(batch)
            target = torch.cat([targets[i] for i in batch])
            loss = loss_fn(F.log_softmax(logits, dim=-1).transpose(0, 1), target,
                           torch.tensor([lengths[i] for i in batch], dtype=torch.long),
                           torch.tensor([len(targets[i]) for i in batch], dtype=torch.long))
            if not torch.isfinite(loss):
                raise ValueError('Non-finite CTC loss; no candidate emitted')
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(trainable, 5)
            optimizer.step()
            losses.append(loss.item())
        dev = metrics([rows[i] for i in evaluation_indices['DEV']], predict(evaluation_indices['DEV']))
        key = (dev['critical_errors'], dev['cer'])
        if key < best_key:
            best_key, best_epoch = key, epoch
            best_state = {k: value.detach().clone() for k, value in model.state_dict().items()}
        history.append({'epoch': epoch, 'mean_ctc_loss': sum(losses) / len(losses), 'dev': dev})
        print(f"Epoch {epoch}/{args.epochs}: DEV CER={dev['cer']:.4f}, "
              f"critical errors={dev['critical_errors']}", flush=True)
    model.load_state_dict(best_state)
    # HOLDOUT is used once for the selected candidate, never for selection.
    predictions = {s: predict(ids) for s, ids in evaluation_indices.items()}
    candidate = {s: metrics([rows[i] for i in ids], predictions[s]) for s, ids in evaluation_indices.items()}
    if any(digest(path) != sha for path, sha in before.items()):
        raise ValueError('Production model bytes changed during the experiment')
    if digest(args.manifest) != manifest_sha256:
        raise ValueError('Reviewed manifest changed during training; no candidate emitted')
    output.mkdir(parents=True)
    (output / 'trainer_snapshot.py').write_bytes(trainer_source)
    (output / 'manifest_snapshot.json').write_bytes(manifest_source)
    torch.save(model.state_dict(), output / 'candidate.pth')
    (output / 'vocab.json').write_text(json.dumps(vocab, ensure_ascii=False, indent=2), encoding='utf-8')
    mode = ('train last CNN block, BiLSTM and CTC head; first three CNN blocks frozen' if train_visual
            else 'frozen CNN; train BiLSTM and CTC head' if train_recurrent
            else 'frozen CNN/BiLSTM; train linear CTC head only')
    evidence = {'schema_version': 1, 'mode': mode,
                'manifest_sha256': manifest_sha256, 'source_model_hashes': before,
                'settings': {'epochs': args.epochs, 'batch_size': args.batch_size,
                             'threads': args.threads, 'learning_rate': args.learning_rate,
                             'preserve_aspect_ratio': preserve_aspect_ratio,
                             'train_recurrent': train_recurrent,
                             'train_last_visual_block': train_visual,
                             'numeric_fields_only': numeric_only,
                             'holdout_deferred': defer_holdout,
                             'augment_train_contrast': augment_contrast},
                'training_views': {'original': len(evaluation_indices['TRAIN']),
                                   'augmented': len(indices['TRAIN'])-len(evaluation_indices['TRAIN']),
                                   'augmentation': 'grayscale autocontrast; TRAIN only' if augment_contrast else None},
                'recognition_scope': 'reviewed unsigned numeric field only; no prose or expressions' if numeric_only else 'reviewed text line or field',
                'input_policy': {'height': 64, 'max_width': 1024,
                                 'resize': 'aspect; stride 8; min width 64' if preserve_aspect_ratio else 'fixed 64x1024',
                                 'padding': 'features only; excluded from CTC, decoding and recurrent context'},
                'trainer_sha256': hashlib.sha256(trainer_source).hexdigest(),
                'seed': args.seed, 'torch_version': torch.__version__, 'device': 'cpu',
                'new_training_characters': new_chars, 'selected_epoch': best_epoch,
                'baseline': baseline, 'candidate': candidate, 'history': history,
                'scope_metrics': {s: {'baseline': scoped_metrics([rows[i] for i in ids], baseline_predictions[s]),
                                     'candidate': scoped_metrics([rows[i] for i in ids], predictions[s])}
                                  for s, ids in evaluation_indices.items()},
                'quality_gate': ({'experiment_passed': False, 'production_promoted': False,
                                  'reasons': ['HOLDOUT deferred; development measurements only'],
                                  'scope': 'TRAIN and DEV only; no HOLDOUT neural inference'}
                                 if defer_holdout else gate(baseline, candidate)),
                'limitations': document.get('limitations', []),
                'predictions': {s: [{'id': rows[i]['id'], 'reference': rows[i]['text'],
                                    'baseline': a, 'candidate': b}
                                   for i, a, b in zip(ids, baseline_predictions[s], predictions[s])]
                                for s, ids in evaluation_indices.items()},
                'candidate_sha256': digest(output / 'candidate.pth')}
    evidence['candidate_vocab_sha256'] = digest(output / 'vocab.json')
    (output / 'evaluation.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'selected_epoch': best_epoch, 'baseline': baseline,
                      'candidate': candidate, 'quality_gate': evidence['quality_gate']}, indent=2))


def evaluate_saved(args):
    """Evaluate a frozen checkpoint without fitting or selecting another epoch."""
    folder, output, model_dir = args.evaluate_candidate.resolve(), args.output.resolve(), args.model_dir.resolve()
    if not 1 <= args.threads <= 8:
        raise ValueError('Use bounded evaluation threads')
    if (output.exists() or output.is_relative_to((ROOT / 'ai/runtime/models').resolve())
            or output.is_relative_to(model_dir) or model_dir.is_relative_to(output)
            or output.is_relative_to(folder) or folder.is_relative_to(output)):
        raise ValueError('Use a fresh evaluation output outside candidate and production models')
    evidence = json.loads((folder / 'evaluation.json').read_text(encoding='utf-8'))
    checkpoint, vocabulary = folder / 'candidate.pth', folder / 'vocab.json'
    if (digest(checkpoint) != evidence['candidate_sha256']
            or digest(vocabulary) != evidence.get('candidate_vocab_sha256')):
        raise ValueError('Candidate checkpoint/vocabulary hash mismatch; older pairs require separate verified review')
    if digest(args.manifest) != evidence['manifest_sha256']:
        raise ValueError('Evaluation must use the frozen reviewed manifest paired with this run')
    weights, base_vocab = model_dir / 'best_cer.pth', model_dir / 'vocab.json'
    for path in (weights, base_vocab):
        if digest(path) != evidence['source_model_hashes'].get(str(path)):
            raise ValueError('Original model hash differs from the experiment baseline')
    before = {path: digest(path) for path in (checkpoint, vocabulary, args.manifest, weights, base_vocab)}
    manifest_source = args.manifest.read_bytes()
    document, samples = load_reviewed(args.manifest, args.data_root)
    if json.loads(manifest_source.decode('utf-8')) != document:
        raise ValueError('Reviewed manifest changed while it was being loaded')
    import torch
    sys.path.insert(0, str(ROOT / 'ai/runtime'))
    from app.ocr.model import CRNN
    torch.set_num_threads(args.threads)
    vocab = json.loads(vocabulary.read_text(encoding='utf-8'))
    original_vocab = json.loads(base_vocab.read_text(encoding='utf-8'))
    candidate_model = CRNN(len(vocab)).eval()
    candidate_model.load_state_dict(torch.load(checkpoint, map_location='cpu', weights_only=True))
    baseline_model = CRNN(len(original_vocab)).eval()
    baseline_model.load_state_dict(torch.load(weights, map_location='cpu', weights_only=True))
    rows, baseline_predictions, predictions = [], [], []
    with torch.no_grad():
        for row, crop in samples:
            if row['split'] not in ('DEV', 'HOLDOUT'):
                continue
            baseline_logits = baseline_model(line_tensor(crop).unsqueeze(0))
            logits = candidate_model(line_tensor(crop, evidence['settings']['preserve_aspect_ratio']).unsqueeze(0))
            baseline_predictions.extend(decode_ctc(baseline_logits.argmax(-1).tolist(), original_vocab))
            predictions.extend(decode_ctc(logits.argmax(-1).tolist(), vocab))
            rows.append(row)
    baseline, candidate, scopes = {}, {}, {}
    for split in ('DEV', 'HOLDOUT'):
        chosen = [i for i, row in enumerate(rows) if row['split'] == split]
        refs = [rows[i] for i in chosen]
        old, new = [baseline_predictions[i] for i in chosen], [predictions[i] for i in chosen]
        baseline[split], candidate[split] = metrics(refs, old), metrics(refs, new)
        scopes[split] = {'baseline': scoped_metrics(refs, old), 'candidate': scoped_metrics(refs, new)}
    result = {'mode': 'frozen checkpoint evaluation; no fitting or checkpoint selection',
              'candidate_sha256': digest(checkpoint), 'candidate_vocab_sha256': digest(vocabulary),
              'manifest_sha256': digest(args.manifest), 'baseline': baseline, 'candidate': candidate,
              'scope_metrics': scopes, 'quality_gate': gate(baseline, candidate),
              'limitations': document.get('limitations', []),
              'predictions': [dict(id=row['id'], split=row['split'], reference=row['text'], baseline=old, candidate=new)
                              for row, old, new in zip(rows, baseline_predictions, predictions)]}
    if any(digest(path) != sha for path, sha in before.items()):
        raise ValueError('Frozen evaluation inputs changed; no result emitted')
    output.mkdir(parents=True)
    (output / 'evaluation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('baseline', 'candidate', 'quality_gate')}, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--data-root', type=Path, default=ROOT / 'ai-training/datasets/drive_math')
    parser.add_argument('--model-dir', type=Path, default=ROOT / 'ai/runtime/models/ocr/crnn_vi_handwriting_v1')
    parser.add_argument('--epochs', type=int, default=12)
    parser.add_argument('--batch-size', type=int, default=4)
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--learning-rate', type=float, default=0.001)
    parser.add_argument('--seed', type=int, default=20261008)
    parser.add_argument('--preserve-aspect-ratio', action='store_true',
                        help='Experimental variable-width input; never changes production preprocessing')
    parser.add_argument('--train-recurrent', action='store_true',
                        help='Also adapt the BiLSTM; CNN remains frozen and no model is installed')
    parser.add_argument('--train-last-visual-block', action='store_true',
                        help='Adapt last CNN block and BiLSTM; first three CNN blocks remain frozen')
    parser.add_argument('--numeric-fields-only', action='store_true',
                        help='Separate unsigned-numeral model; requires declared numeric fields in every split')
    parser.add_argument('--defer-holdout', action='store_true',
                        help='Develop using TRAIN/DEV only; do not infer on HOLDOUT or pass a release gate')
    parser.add_argument('--augment-train-contrast', action='store_true',
                        help='One grayscale/autocontrast TRAIN view; originals and evaluation pixels stay unchanged')
    parser.add_argument('--evaluate-candidate', type=Path,
                        help='Evaluate this frozen paired checkpoint; no training or epoch selection')
    arguments = parser.parse_args()
    if arguments.evaluate_candidate:
        evaluate_saved(arguments)
    else:
        run(arguments)
