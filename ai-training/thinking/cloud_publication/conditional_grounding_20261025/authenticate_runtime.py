from google.colab import auth
import google.auth
from googleapiclient.discovery import build
import json

auth.authenticate_user()
recovery_credentials, _ = google.auth.default()
recovery_drive = build('drive', 'v3', credentials=recovery_credentials,
                       cache_discovery=False)
who = recovery_drive.about().get(fields='user(displayName,emailAddress)').execute()
source_metadata = recovery_drive.files().get(
    fileId='1Twd75htZfKKSKvjJ4j4imAu_sca7UJ1c',
    fields='id,name,size,trashed', supportsAllDrives=True).execute()
assert source_metadata['id'] == '1Twd75htZfKKSKvjJ4j4imAu_sca7UJ1c'
assert not source_metadata.get('trashed')
print(json.dumps({'drive_authenticated': True, 'user': who['user'],
                  'training_source_metadata': source_metadata,
                  'model_loaded': False, 'training_started': False}))
