"""Explicit native Transformers/PEFT backend; no Unsloth speed claims."""
class NativeBackend:
    @staticmethod
    def from_pretrained(model_name, revision, use_exact_model_name,
                        max_seq_length, dtype, load_in_4bit,
                        quantization_config, attn_implementation):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from huggingface_hub import hf_hub_download, snapshot_download
        from pathlib import Path, PurePosixPath
        import hashlib,json
        if not use_exact_model_name or not load_in_4bit or model_name!='Qwen/Qwen3-1.7B':
            raise ValueError('Expected pinned Qwen3 4bit source')
        if len(revision)!=40 or any(c not in '0123456789abcdef' for c in revision):
            raise ValueError('Expected an immutable lowercase commit hash')
        index_path=Path(hf_hub_download(model_name,'model.safetensors.index.json',revision=revision))
        if index_path.parent.name!=revision:
            raise ValueError('Weight index was not fetched from the exact pinned commit')
        index=json.loads(index_path.read_bytes())
        shards=sorted(set(index['weight_map'].values()))
        if not shards or any(not isinstance(name,str) or PurePosixPath(name).name!=name or '/' in name or '\\' in name for name in shards):
            raise ValueError('Unsafe or empty checkpoint shard list')
        metadata=['config.json','tokenizer.json','model.safetensors.index.json','tokenizer_config.json',
                  'special_tokens_map.json','vocab.json','merges.txt','generation_config.json']
        allow_patterns=sorted(set(metadata+shards))
        snapshot=Path(snapshot_download(model_name,revision=revision,allow_patterns=allow_patterns))
        if snapshot.name!=revision:
            raise ValueError('Downloaded snapshot directory does not equal the pinned commit')
        if not index_path.read_bytes()==(snapshot/'model.safetensors.index.json').read_bytes():
            raise ValueError('Downloaded snapshot index differs from the pinned index')
        resolved={name:snapshot/name for name in metadata if (snapshot/name).is_file()}
        required={'config.json','tokenizer.json','model.safetensors.index.json'}
        if not required.issubset(resolved):raise ValueError('Pinned snapshot is missing required model/tokenizer metadata')
        if any(not (snapshot/name).is_file() for name in shards):
            raise ValueError('Pinned snapshot is missing a listed checkpoint shard')
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
            'weight_shards':shards,'requested_allow_patterns':allow_patterns,'fresh_snapshot_download':True,'local_files_only_load':True,
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
