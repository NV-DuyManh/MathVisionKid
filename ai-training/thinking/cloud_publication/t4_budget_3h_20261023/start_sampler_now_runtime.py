import google.auth,json
from googleapiclient.discovery import build
_sampling_creds,_=google.auth.default()
independentDriveAPI=build('drive','v3',credentials=_sampling_creds,cache_discovery=False)
INVENTORY_PATH=budget_root/'sampling_metadata_inventory.json'
print(json.dumps(launch_t4_sampler()))
