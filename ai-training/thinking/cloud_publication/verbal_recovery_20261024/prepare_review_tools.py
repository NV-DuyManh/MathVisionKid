from pathlib import Path
p=Path(__file__).parent;old=p.parent/'quality_recovery_20261024'
for name in ['capture_dev_runtime.py','decode_dev_receipt.py','assemble_review_gate.py','show_pairs.py']:
 text=(old/name).read_text(encoding='utf8').replace('/content/mathvisionkid_quality_recovery_20261024','/content/mathvisionkid_verbal_recovery_20261024')
 compile(text,name,'exec');(p/name).write_text(text,encoding='utf8')
print('Prepared bounded actual-output capture and root semantic gate tools; no runtime calls.')
