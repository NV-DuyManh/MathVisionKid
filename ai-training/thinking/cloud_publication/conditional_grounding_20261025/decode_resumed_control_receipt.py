from pathlib import Path
P=Path(__file__).parent
code=(P/'decode_control_receipt.py').read_text(encoding='utf8').replace('control_raw_receipt_capture.json','control_resumed_receipt_capture.json').replace("P/'control_phase_verified'","P/'control_resumed_verified'")
exec(compile(code,__file__,'exec'))
