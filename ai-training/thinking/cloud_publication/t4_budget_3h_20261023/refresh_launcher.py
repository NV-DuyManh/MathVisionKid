import base64, hashlib, pathlib
base = pathlib.Path(r'D:\nhom6\train thử\MathVisionKid\ai-training\thinking\cloud_publication\t4_budget_3h_20261023')
worker = (base / 'sampling' / 'colab_train_view_worker.py').read_bytes()
launcher = base / 'start_cpu_stratified_sampler_launcher.py'
s = launcher.read_text(encoding='utf-8')
start = s.index("WORKER_B64 = '")
end = s.index("\n", start)
s = s[:start] + "WORKER_B64 = '" + base64.b64encode(worker).decode('ascii') + "'" + s[end:]
start = s.index('WORKER_SHA256 = "')
end = s.index('\n', start)
s = s[:start] + 'WORKER_SHA256 = "' + hashlib.sha256(worker).hexdigest() + '"' + s[end:]
launcher.write_text(s, encoding='utf-8')
print('worker bytes', len(worker), 'sha256', hashlib.sha256(worker).hexdigest(), 'launcher bytes', launcher.stat().st_size)
