import pathlib,json
p=pathlib.Path('/content/mathvisionkid_recovery_20261026/four_controls_publication_status.json')
v=json.loads(p.read_bytes());print(json.dumps({k:v.get(k) for k in ['state','error','traceback','work','canonical_context_sha256'] if k in v},ensure_ascii=False))
