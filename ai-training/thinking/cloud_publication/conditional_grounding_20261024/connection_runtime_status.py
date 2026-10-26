"""Read-only Colab runtime observation. Never authenticate, train, or load weights."""
import datetime
import json
import pathlib
import subprocess
import sys

runtime_observation = {
    'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'purpose': 'read_only_after_mcp_connection',
    'python_version': sys.version.split()[0],
    'colab_module_already_loaded': 'google.colab' in sys.modules,
    'torch_module_already_loaded': 'torch' in sys.modules,
    'credentials_globals_present': {
        name: name in globals()
        for name in ('credentials', 'recovery_credentials')
    },
    'model_globals_present': {
        name: name in globals()
        for name in ('model', 'recovery_model', 'base_model')
    },
    'known_previous_work_directories_exist': {
        path: pathlib.Path(path).is_dir()
        for path in (
            '/content/mathvisionkid_skill_recovery_150m_20261024',
            '/content/mathvisionkid_verbal_recovery_20261024',
        )
    },
    'worker_processes': {},
    'model_weights_loaded_by_this_cell': False,
    'optimizer_or_training_started_by_this_cell': False,
}
for process_name in ('skill_training_process', 'recovery_process',
                     'native_probe_process', 'fewshot_process'):
    process = globals().get(process_name)
    if isinstance(process, subprocess.Popen):
        runtime_observation['worker_processes'][process_name] = {
            'pid': process.pid, 'exit_code': process.poll()
        }
    else:
        runtime_observation['worker_processes'][process_name] = 'not_bound'
try:
    gpu = subprocess.run(
        ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu',
         '--format=csv,noheader,nounits'], capture_output=True, text=True,
        timeout=10, check=False)
    runtime_observation['gpu_query_exit_code'] = gpu.returncode
    runtime_observation['gpu_query'] = gpu.stdout.strip()[:1200]
except (OSError, subprocess.TimeoutExpired) as error:
    runtime_observation['gpu_query_error'] = type(error).__name__
print(json.dumps(runtime_observation, ensure_ascii=False))
