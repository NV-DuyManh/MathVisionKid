"""Scan JSONL source metadata completely, without loading corpus images/APIs.

OCR labels/student work are not promoted to correct mathematical solutions.
"""
import argparse
import json
from pathlib import Path

def inventory(roots,output):
    reports=[]; seen=set()
    for source in roots:
        root=Path(source)
        if not root.exists():
            reports.append({'root':str(root),'exists':False}); continue
        files=sorted(root.rglob('*.jsonl'))
        for file in files:
            resolved=str(file.resolve())
            if resolved in seen: continue
            seen.add(resolved)
            item={'path':str(file),'rows':0,'json_errors':0,'ocr_text_rows':0,
                  'explicit_solution_candidates':0,'human_verified_solution_candidates':0,
                  'complete_scan':False}
            try:
                with file.open(encoding='utf-8-sig') as stream:
                    for line in stream:
                        if not line.strip(): continue
                        item['rows']+=1
                        try: row=json.loads(line)
                        except (ValueError,TypeError): item['json_errors']+=1; continue
                        if not isinstance(row,dict): item['json_errors']+=1; continue
                        item['ocr_text_rows']+=bool(row.get('text') or row.get('transcription_verbatim'))
                        # Candidate only; this does not validate provenance or correctness.
                        candidate=bool(row.get('problem') and row.get('solution') and row.get('expected_answer') is not None)
                        item['explicit_solution_candidates']+=candidate
                        item['human_verified_solution_candidates']+=candidate and row.get('human_verified') is True
                item['complete_scan']=True
            except (OSError,UnicodeError) as exc: item['error']=type(exc).__name__
            reports.append(item)
        if not files: reports.append({'root':str(root),'exists':True,'jsonl_files':0})
    report={'mode':'all_jsonl_rows_under_explicit_roots_only','files':reports,
            'scanned_files':len(seen),'no_image_or_archive_content_scanned':True,
            'limitations':['Columns other than problem/solution/expected_answer require manual schema mapping.',
                           'Candidate labels are not verified solutions or teacher-certified gold.']}
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--roots',nargs='+',required=True); p.add_argument('--output',required=True)
    args=p.parse_args(); print(json.dumps(inventory(args.roots,args.output),ensure_ascii=False,indent=2))
