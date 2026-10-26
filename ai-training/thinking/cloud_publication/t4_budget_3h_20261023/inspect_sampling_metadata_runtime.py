import pathlib,json,zipfile,io
root=pathlib.Path('/content/mathvisionkid_full_text_training')
out={}
with zipfile.ZipFile(root/'published_progress.zip') as z:
    ready=json.loads(z.read('full_text_training_release_20261023/release_manifest.json'))
    out['release']=ready
    recipe=json.loads(z.read(ready['recipe_pointer']['member']))
    out['recipe_keys']=list(recipe)
    out['chat_member_metadata']=recipe['chat_members']
    out['artifact_metadata']=recipe['artifacts']
    out['source_member_sample']=recipe.get('source_members',[])[:5]
    out['source_candidate_manifest']=json.loads(z.read(ready['source_candidate_manifest']['member']))
    out['metadata_members']=[dict(name=i.filename,bytes=i.file_size) for i in z.infolist() if any(k in i.filename for k in ('catalog','blueprint','coverage','manifest','curriculum','candidate','index')) and i.file_size<2000000 and not any(k in i.filename.lower() for k in ('challenge','frozen','pilot','eval'))][-100:]
out['runtime_files']=[dict(name=str(p.relative_to(root)),bytes=p.stat().st_size) for p in root.rglob('*') if p.is_file() and p.parent.name in ('payload_cache','run_artifacts') and not p.name.endswith('.pt')][:25]
(budget_root/'sampling_metadata_inventory.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False))
