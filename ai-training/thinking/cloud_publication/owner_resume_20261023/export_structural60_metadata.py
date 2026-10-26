import json,hashlib,io,zipfile,base64
_initial_recipe_path=_repair_dir/'publish_latest_union_recipe.json'
(_repair_dir/'initial_unmerged_recipe_provenance.json').write_bytes(_initial_recipe_path.read_bytes())
_repair_extra=repair_recipe.pop('derived_structural60_repair')
(_repair_dir/'derived_recipe_provenance.json').write_text(json.dumps(_repair_extra,ensure_ascii=False,indent=2))
_recipe_bytes=(json.dumps(repair_recipe,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
repair_recipe_sha256=hashlib.sha256(_recipe_bytes).hexdigest()
_initial_recipe_path.write_bytes(_recipe_bytes)
_prepared=json.loads((_repair_dir/'repair_recipe_prepared.json').read_bytes());_prepared['recipe_sha256']=repair_recipe_sha256;_prepared['identity']=audit_v3.plan_identity(repair_recipe)
(_repair_dir/'repair_recipe_prepared.json').write_text(json.dumps(_prepared,ensure_ascii=False,indent=2))
_names=['repair_receipt.json','derived_artifact_remote_verified.json','publish_latest_union_recipe.json','repair_recipe_prepared.json','derived_recipe_provenance.json']
_buffer=io.BytesIO();_refs=[]
with zipfile.ZipFile(_buffer,'w',zipfile.ZIP_DEFLATED) as _zip:
 for _name in _names:
  _b=(_repair_dir/_name).read_bytes();assert len(_b)<1024*1024
  _zip.writestr(_name,_b);_refs.append({'name':_name,'bytes':len(_b),'sha256':hashlib.sha256(_b).hexdigest()})
_b=_buffer.getvalue();assert len(_b)<1024*1024
print(json.dumps({'schema':'MathVisionKid.bounded_repair_metadata_export.v1','files':_refs,'bytes':len(_b),'sha256':hashlib.sha256(_b).hexdigest(),'zip_b64':base64.b64encode(_b).decode(),'corpus_or_sqlite_downloaded':False}))
