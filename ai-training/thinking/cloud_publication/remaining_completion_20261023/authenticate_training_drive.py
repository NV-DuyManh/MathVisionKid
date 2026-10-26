from google.colab import auth
import google.auth
from googleapiclient.discovery import build
import json
auth.authenticate_user()
_text_credentials,_text_project=google.auth.default()
text_training_drive=build('drive','v3',credentials=_text_credentials,cache_discovery=False)
_text_target=text_training_drive.files().get(fileId='1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme',fields='id,name',supportsAllDrives=True).execute()
assert _text_target['id']=='1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme'
print(json.dumps({'drive_authenticated':True,'existing_state_access_verified':True,'training_started':False}))
