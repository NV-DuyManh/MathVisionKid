"""Offline formula probe: original Drive pixels stay in RAM, models stay private.

Labels and layout roles come from an existing review. Formula pair boxes are
proposals until visually checked. No hypothesis becomes a training label.
"""
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import time
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/'ai-training/datasets/drive_math'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def group(text, start):
    if start >= len(text) or text[start] != '{':
        return None
    depth = 1
    for end in range(start+1, len(text)):
        depth += (text[end] == '{') - (text[end] == '}')
        if not depth:
            return text[start+1:end], end+1
    return None


def normalize_math(text):
    text = unicodedata.normalize('NFC', text).strip().strip('$')
    replacements = {r'\left':'', r'\right':'', r'\displaystyle':'', r'\textstyle':'',
        r'\dfrac':r'\frac', r'\tfrac':r'\frac', r'\times':'×', r'\div':':',
        r'\colon':':', r'\cdot':'·', r'\leq':'≤', r'\geq':'≥', r'\neq':'≠',
        r'\,':'', r'\;':'', r'\!':'', r'\:':'', r'\quad':'', r'\ ':'',
        '−':'-', '÷':':', '²':'^2', '³':'^3'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'\\(?:mathrm|text|operatorname)\{([^{}]*)\}', r'\1', text)
    text = re.sub(r'\s+', '', text)
    text = re.sub(r'(?<![A-Za-z0-9])(-?\d+)/(-?\d+)(?![A-Za-z0-9])',
                  lambda m:f'frac({m[1]},{m[2]})', text)
    while r'\frac{' in text:
        start = text.index(r'\frac{')
        numerator = group(text, start+5)
        denominator = group(text, numerator[1]) if numerator else None
        if denominator is None:
            break
        replacement = f'frac({normalize_math(numerator[0])},{normalize_math(denominator[0])})'
        text = text[:start]+replacement+text[denominator[1]:]
    # TeX braces are presentation groups. Parentheses and all digits remain.
    return text.replace('{', '').replace('}', '')


def fraction_parts(text):
    text = text.strip().strip('$').replace(r'\dfrac', r'\frac').replace(r'\tfrac', r'\frac')
    text = text.replace(r'\displaystyle', '').strip()
    if not text.startswith(r'\frac'):
        return None
    numerator = group(text, 5)
    denominator = group(text, numerator[1]) if numerator else None
    if not denominator or text[denominator[1]:].strip():
        return None
    parts = normalize_math(numerator[0]), normalize_math(denominator[0])
    return parts if all(parts) else None


def pair_fraction_components(rows):
    candidates = []
    for n in rows:
        if n.get('math_role') != 'numerator':
            continue
        a = n['box']
        for d in rows:
            if (d.get('math_role') != 'denominator' or n['split'] != d['split']
                    or n['source']['sha256'] != d['source']['sha256']):
                continue
            b = d['box']
            overlap = max(0, min(a[2],b[2])-max(a[0],b[0]))
            width = min(a[2]-a[0],b[2]-b[0])
            gap = b[1]-a[3]
            if width > 0 and overlap/width >= .5 and 0 <= gap <= 2.5*max(a[3]-a[1],b[3]-b[1]):
                candidates.append((n['id'], d['id']))
    return [(n,d) for n,d in candidates if sum(a==n for a,b in candidates)==1
            and sum(b==d for a,b in candidates)==1]


def freeze(folder):
    folder = Path(folder)
    path = folder/'cohort.json'
    if path.exists():
        raise FileExistsError('Preserve frozen cohort')
    policy_path = DATA/'math_data_expansion_20261017/policy.json'
    comparison_path = DATA/'specialist_comparison_v2_20261022/comparison.json'
    policy = read(policy_path)
    comparison = read(comparison_path)
    assert sha(policy_path) == comparison['policy_sha256']
    indexed = {p['id']:p for p in comparison['predictions']}
    roles = {'expression','comparison_expression','denominator','numerator','numeric_component',
             'numeric_field','math_expression','intermediate','dividend','divisor','quotient','remainder','multiplier'}
    selected = [r for r in policy['records'] if r['review_status']=='verified' and not r['uncertain']
                and (r['split']=='DEV' and r.get('math_role') in roles
                     or r.get('math_role') in {'numerator','denominator'})]
    items = []
    byid = {r['id']:r for r in selected}
    for row in selected:
        assert row['source']['sha256'] not in policy['forbidden_source_hashes']
        prior = indexed[row['id']]
        items.append(dict(id=row['id'],kind='component',row=row,
            reference=row['text'],baseline=prior['hypotheses']['math'],
            source=row['source'],split=row['split'],box=row['box'],
            crop_pixels_sha256=prior['crop_pixels_sha256'],crop_size=prior['crop_size']))
    pairs = pair_fraction_components(selected)
    for n_id,d_id in pairs:
        n,d = byid[n_id],byid[d_id]
        a,b = n['box'],d['box']
        pad = round(.25*max(a[2]-a[0],b[2]-b[0],a[3]-a[1],b[3]-b[1]))
        box = [min(a[0],b[0])-pad,min(a[1],b[1])-pad,
               max(a[2],b[2])+pad,max(a[3],b[3])+pad]
        items.append(dict(id='fraction:'+n_id+'|'+d_id,kind='fraction',
            reference=[n['text'],d['text']],
            baseline=[indexed[n_id]['hypotheses']['math'],indexed[d_id]['hypotheses']['math']],
            source=n['source'],split=n['split'],box=box,
            component_ids=[n_id,d_id],geometry_reviewed=False))
    pinned = [Path(__file__),ROOT/'scripts/data/test_formula_probe.py',policy_path,comparison_path,
              ROOT/'scripts/data/source_orientation.py',ROOT/'scripts/data/finetune_line_ocr.py',
              DATA/'math_all_20261013/math_focus/source_worker_raw.py',
              DATA/'math_all_20261013/drive_stream.py']
    plan = dict(items=items,input_hashes={str(p):sha(p) for p in pinned},
        forbidden_source_hashes=policy['forbidden_source_hashes'],
        source_images_written=0,training=False,production_promoted=False,
        fraction_pairing='unique reciprocal overlap >=0.5, denominator below numerator; reviewed roles, not labels',
        limits=['Repeated development sources, not independent validation',
                'Component crops and roles supplied by earlier review',
                'Formula pair geometry requires source visual review',
                'Only 73 DEV math regions, no claim about all Student OCR'])
    path.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(components=len(selected),pairs=len(pairs),requests=len(items))))


def run(cohort, model_dir, output):
    import cv2
    import numpy as np
    from PIL import Image
    from paddleocr import FormulaRecognition
    sys.path[:0] = [str(ROOT/'scripts/data'),str(ROOT/'ai/runtime'),
                   str(DATA/'math_all_20261013/math_focus'),str(DATA/'math_all_20261013'),
                   str(DATA/'math_all_20261013/math_layout_retry_20261013/tables')]
    from source_worker_raw import SourceWorker
    from source_orientation import orient_image
    from table_cells_v3 import rectify_cell
    cohort,model_dir,output = Path(cohort),Path(model_dir),Path(output)
    if output.exists():
        raise FileExistsError('Preserve inference evidence')
    output.mkdir(parents=True)
    plan = read(cohort)
    assert all(sha(p)==h for p,h in plan['input_hashes'].items())
    model_files = {str(p):sha(p) for p in model_dir.iterdir() if p.is_file()}
    name = model_dir.name.removesuffix('_infer')
    model = FormulaRecognition(model_name=name,model_dir=str(model_dir),
                               device='cpu',enable_mkldnn=False,cpu_threads=4)
    groups = {}
    for item in plan['items']:
        assert item['source']['sha256'] not in plan['forbidden_source_hashes']
        groups.setdefault(item['source']['sha256'],[]).append(item)
    worker = SourceWorker(timeout=45)
    predictions=[];failures=[];receipts=[];started=time.monotonic()
    try:
        with (output/'predictions.jsonl').open('x',encoding='utf8') as stream:
            for items in groups.values():
                source=items[0]['source']
                try:
                    raw=worker.read(dict(kind='file',path=source['mounted_source_path']))
                    assert hashlib.sha256(raw).hexdigest()==source['sha256']
                    with Image.open(io.BytesIO(raw)) as image:
                        page=orient_image(image,source)
                    receipts.append(dict(drive_id=source['drive_id'],sha256=source['sha256']))
                    for item in items:
                        if time.monotonic()-started > 900:
                            raise TimeoutError('Frozen 15-minute inference budget exhausted')
                        box=item['box']
                        box=[max(0,box[0]),max(0,box[1]),min(page.width,box[2]),min(page.height,box[3])]
                        row=item.get('row',{})
                        if 'rectified_cell' in row:
                            crop=Image.fromarray(cv2.cvtColor(rectify_cell(cv2.cvtColor(np.asarray(page),cv2.COLOR_RGB2BGR),
                                row['rectified_cell']),cv2.COLOR_BGR2RGB))
                        else:
                            crop=page.crop(box)
                        crop_hash=hashlib.sha256(crop.tobytes()).hexdigest()
                        if item['kind']=='component':
                            assert crop_hash==item['crop_pixels_sha256'] and list(crop.size)==item['crop_size']
                        before=time.monotonic()
                        result=list(model.predict(input=np.asarray(crop)[:,:,::-1].copy(),batch_size=1))
                        latex=result[0]['rec_formula']
                        if item['kind']=='fraction':
                            parsed=fraction_parts(latex)
                            expected=tuple(normalize_math(t) for t in item['reference'])
                            baseline=tuple(normalize_math(t) for t in item['baseline'])
                            exact=parsed==expected
                            normalized=parsed
                        else:
                            expected=normalize_math(item['reference']);baseline=normalize_math(item['baseline'])
                            normalized=normalize_math(latex);exact=normalized==expected
                        record=dict(id=item['id'],kind=item['kind'],split=item['split'],
                            role=row.get('math_role'),source_sha256=source['sha256'],drive_id=source['drive_id'],
                            box=box,crop_size=list(crop.size),crop_pixels_sha256=crop_hash,
                            reference=item['reference'],baseline_raw=item['baseline'],raw_latex=latex,
                            expected_normalized=expected,baseline_normalized=baseline,
                            candidate_normalized=normalized,baseline_exact=baseline==expected,
                            candidate_exact=exact,seconds=time.monotonic()-before,
                            status='MODEL_DRAFT',training_eligible=False)
                        predictions.append(record)
                        stream.write(json.dumps(record,ensure_ascii=False)+'\n');stream.flush()
                        if len(predictions)%10==0:
                            print(f'{name}: {len(predictions)}/{len(plan["items"])} requests',flush=True)
                    del page
                except (OSError,RuntimeError,ValueError,AssertionError,TimeoutError) as exc:
                    done={r['id'] for r in predictions}
                    failures.extend(dict(id=i['id'],error=type(exc).__name__+': '+str(exc)) for i in items if i['id'] not in done)
    finally:
        worker.close()
    assert all(sha(p)==h for p,h in model_files.items())
    assert all(sha(p)==h for p,h in plan['input_hashes'].items())
    scopes={}
    for split in ('TRAIN','DEV'):
        for scope in ('components','fraction_components','fraction_pairs'):
            chosen=[p for p in predictions if p['split']==split and (
                scope=='components' and p['kind']=='component' or
                scope=='fraction_components' and p['role'] in {'numerator','denominator'} or
                scope=='fraction_pairs' and p['kind']=='fraction')]
            scopes[split+'/'+scope]=dict(requests=len(chosen),
                baseline_exact=sum(p['baseline_exact'] for p in chosen),
                candidate_exact=sum(p['candidate_exact'] for p in chosen),
                corrected=sum(not p['baseline_exact'] and p['candidate_exact'] for p in chosen),
                regressed=sum(p['baseline_exact'] and not p['candidate_exact'] for p in chosen))
    result=dict(completed=len(predictions)==len(plan['items']),requested=len(plan['items']),inferred=len(predictions),
        model=name,model_hashes=model_files,cohort_sha256=sha(cohort),scopes=scopes,
        failures=failures,source_receipts=receipts,predictions_sha256=sha(output/'predictions.jsonl'),
        elapsed_seconds=time.monotonic()-started,source_images_written=0,training=False,
        production_promoted=False,limits=plan['limits'])
    (output/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(model=name,inferred=len(predictions),failures=len(failures),scopes=scopes)),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['freeze','run'])
    parser.add_argument('--folder',type=Path)
    parser.add_argument('--cohort',type=Path)
    parser.add_argument('--model-dir',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.action=='freeze':
        freeze(args.folder)
    else:
        run(args.cohort,args.model_dir,args.output)
