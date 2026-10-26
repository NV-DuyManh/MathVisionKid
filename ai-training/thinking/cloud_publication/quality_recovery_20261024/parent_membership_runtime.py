import json
print(json.dumps(recovery_drive.files().list(q="'19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n' in parents and name='MathVisionKid_QUALITY_RECOVERY_20261024' and trashed=false",fields='files(id,name,mimeType,parents)').execute()))
