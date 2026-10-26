from pathlib import Path
p=Path(__file__).parent
(p/'capture_step1_runtime.py').write_text('recovery_capture_step=1\n'+(p/'capture_dev_runtime.py').read_text(encoding='utf8'),encoding='utf8')
