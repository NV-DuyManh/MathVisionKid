import json
parent='19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n'
name='MathVisionKid_QUALITY_RECOVERY_20261024'
print(json.dumps({'parent':recovery_drive.files().get(fileId=parent,fields='id,name,mimeType,parents,trashed,capabilities(canAddChildren)').execute(),'folders':recovery_drive.files().list(q="name='"+name+"' and trashed=false",fields='files(id,name,mimeType,parents,trashed,capabilities(canAddChildren))').execute()},ensure_ascii=False))
