from pathlib import Path
import hashlib,json
P=Path(__file__).parent
backend=(P/'native_backend.py').read_text(encoding='utf8')
old="""        from transformers import AutoModelForCausalLM, AutoTokenizer
        assert use_exact_model_name and load_in_4bit
        tokenizer=AutoTokenizer.from_pretrained(model_name,revision=revision)
        model=AutoModelForCausalLM.from_pretrained(
            model_name,revision=revision,device_map={'':0},
            dtype=dtype,quantization_config=quantization_config,
            attn_implementation=attn_implementation)
        return model,tokenizer"""
new="""        from transformers import AutoModelForCausalLM, AutoTokenizer
        from transformers.utils.hub import cached_file
        from pathlib import Path
        import hashlib,json
        if not use_exact_model_name or not load_in_4bit or model_name!='Qwen/Qwen3-1.7B':
            raise ValueError('Expected pinned Qwen3 4bit source')
        resolved={name:Path(cached_file(model_name,name,revision=revision))
                  for name in ('config.json','tokenizer.json','model.safetensors.index.json')}
        if any(path.parent.name!=revision for path in resolved.values()):
            raise ValueError('Hub cached snapshot is not the explicit pinned revision')
        snapshot=resolved['config.json'].parent
        if any(path.parent!=snapshot for path in resolved.values()):
            raise ValueError('Model and tokenizer snapshots differ')
        index=json.loads(resolved['model.safetensors.index.json'].read_bytes())
        shards=sorted(set(index['weight_map'].values()))
        for name in shards:
            if Path(name).name!=name or not (snapshot/name).is_file():
                raise ValueError('Missing or unsafe pinned checkpoint shard')
        tokenizer=AutoTokenizer.from_pretrained(str(snapshot),local_files_only=True)
        model=AutoModelForCausalLM.from_pretrained(
            str(snapshot),local_files_only=True,device_map={'':0},
            dtype=dtype,quantization_config=quantization_config,
            attn_implementation=attn_implementation)
        model._mathvisionkid_artifact_revision=revision
        model._mathvisionkid_artifact_proof={
            'requested_model':model_name,'requested_revision':revision,
            'loaded_from_pinned_snapshot_directory':True,
            'snapshot_directory_revision':snapshot.name,
            'metadata_sha256':{name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in resolved.items()},
            'weight_shards':shards,'local_files_only_load':True,
            'tokenizer_eos_id':tokenizer.eos_token_id,
            'legacy_config_commit_hash':getattr(model.config,'_commit_hash',None)}
        return model,tokenizer"""
assert backend.count(old)==1
backend=backend.replace(old,new)
worker=(P/'recovery_worker_v3.py').read_text(encoding='utf8')
worker=worker.replace('from native_backend import NativeBackend as FastLanguageModel',
                      'from native_backend_v2 import NativeBackend as FastLanguageModel')
old=" if getattr(model.config,'_commit_hash',None)!=REV or tok.eos_token_id!=151645:raise ValueError('model/tokenizer revision mismatch')"
new=""" atomic(out/'model_artifact_binding.json',model._mathvisionkid_artifact_proof)
 if getattr(model,'_mathvisionkid_artifact_revision',None)!=REV or tok.eos_token_id!=151645:raise ValueError('verified snapshot/tokenizer revision mismatch')"""
assert worker.count(old)==1
worker=worker.replace(old,new)
for name,text in [('native_backend_v2.py',backend),('recovery_worker_v4.py',worker)]:
 compile(text,name,'exec');target=P/name
 assert not target.exists(), 'Versioned repair already built; inspect before replacing'
 target.write_bytes(text.encode())
proof={'schema':'MathVisionKid.native_snapshot_binding_repair.v1',
 'reason':'Transformers5.20.2 leaves private _commit_hash unset. Actual cached config/tokenizer/index paths all match pinned revision; load directly from that snapshot with local_files_only and bind the proof.',
 'prior_attempt_optimizer_updates':0,'previous_frozen_files_preserved':True,
 'new_files':{n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ['native_backend_v2.py','recovery_worker_v4.py']},
 'targets_answers_source_or_quality_gate_changed':False,'model_revision_changed':False}
(P/'code_repair_snapshot_binding.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
