from google.colab import auth
auth.authenticate_user()
import google.auth
from googleapiclient.discovery import build
recovery_credentials,_=google.auth.default()
recovery_drive=build('drive','v3',credentials=recovery_credentials,cache_discovery=False)
print({'drive_access_verified':recovery_drive.files().get(fileId='19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n',fields='id,name',supportsAllDrives=True).execute(),'training_started':False})
