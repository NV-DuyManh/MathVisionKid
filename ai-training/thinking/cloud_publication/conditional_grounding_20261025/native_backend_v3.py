"""Explicit native Transformers/PEFT backend; no Unsloth speed claims."""
class NativeBackend:
    @staticmethod
    def from_pretrained(model_name, revision, use_exact_model_name,
                        max_seq_length, dtype, load_in_4bit,
                        quantization_config, attn_implementation):
        from transformers import AutoModelForCausalLM, AutoTokenizer
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
        return model,tokenizer

    @staticmethod
    def get_peft_model(model,r,lora_alpha,lora_dropout,bias,target_modules,
                       use_gradient_checkpointing,random_state,use_rslora,
                       loftq_config):
        import torch
        from peft import get_peft_model, LoraConfig, prepare_model_for_kbit_training
        assert use_gradient_checkpointing and not use_rslora and loftq_config is None
        torch.manual_seed(random_state)
        model=prepare_model_for_kbit_training(model,use_gradient_checkpointing=True,gradient_checkpointing_kwargs={'use_reentrant':False})
        config=LoraConfig(r=r,lora_alpha=lora_alpha,lora_dropout=lora_dropout,
                          bias=bias,target_modules=target_modules,
                          task_type='CAUSAL_LM',use_rslora=False)
        return get_peft_model(model,config)

    @staticmethod
    def for_inference(model):
        model.eval();model.config.use_cache=True

    @staticmethod
    def for_training(model):
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});model.train();model.config.use_cache=False
