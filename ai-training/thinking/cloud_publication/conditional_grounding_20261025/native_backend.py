"""Explicit native Transformers/PEFT backend; no Unsloth speed claims."""
class NativeBackend:
    @staticmethod
    def from_pretrained(model_name, revision, use_exact_model_name,
                        max_seq_length, dtype, load_in_4bit,
                        quantization_config, attn_implementation):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        assert use_exact_model_name and load_in_4bit
        tokenizer=AutoTokenizer.from_pretrained(model_name,revision=revision)
        model=AutoModelForCausalLM.from_pretrained(
            model_name,revision=revision,device_map={'':0},
            dtype=dtype,quantization_config=quantization_config,
            attn_implementation=attn_implementation)
        return model,tokenizer

    @staticmethod
    def get_peft_model(model,r,lora_alpha,lora_dropout,bias,target_modules,
                       use_gradient_checkpointing,random_state,use_rslora,
                       loftq_config):
        import torch
        from peft import get_peft_model, LoraConfig, prepare_model_for_kbit_training
        assert not use_gradient_checkpointing and not use_rslora and loftq_config is None
        torch.manual_seed(random_state)
        model=prepare_model_for_kbit_training(model,use_gradient_checkpointing=False)
        config=LoraConfig(r=r,lora_alpha=lora_alpha,lora_dropout=lora_dropout,
                          bias=bias,target_modules=target_modules,
                          task_type='CAUSAL_LM',use_rslora=False)
        return get_peft_model(model,config)

    @staticmethod
    def for_inference(model):
        model.eval();model.config.use_cache=True

    @staticmethod
    def for_training(model):
        model.train();model.config.use_cache=False
