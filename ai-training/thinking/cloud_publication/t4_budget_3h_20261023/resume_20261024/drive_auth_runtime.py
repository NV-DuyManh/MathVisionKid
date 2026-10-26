from google.colab import auth
auth.authenticate_user()
import google.auth,json
from googleapiclient.discovery import build
repair_credentials,_=google.auth.default()
repair_drive=build('drive','v3',credentials=repair_credentials,cache_discovery=False)
print(json.dumps({'authenticated':True,'profile':repair_drive.about().get(fields='user(emailAddress,displayName)').execute(),'no_training_started':True},ensure_ascii=False))
