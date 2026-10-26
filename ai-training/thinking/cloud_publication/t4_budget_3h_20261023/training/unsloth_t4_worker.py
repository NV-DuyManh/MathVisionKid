#!/usr/bin/env python3
"""Isolated Qwen3-1.7B Unsloth T4 benchmark/training worker.

Run only in the separately pinned venv. No Drive or network writes are performed.
The train view is an explicit JSONL of accepted train chat rows; evaluation input
is consumed only by the standalone generation fixture routine.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, os, random, shutil, sys, time, zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODEL = "Qwen/Qwen3-1.7B"
REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
RECIPE_SHA256 = "1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8"
EXPECTED_CHAT_MEMBERS = 32
EXPECTED_TRAIN_ROWS = 6502344
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
MODES = {"worked_solution", "hint_level_1", "hint_level_2", "hint_level_3"}
EFFECTIVE_BATCH = 16
RESERVE_SECONDS = 1500


def sha_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""): h.update(block)
    return h.hexdigest()


def atomic_json(path: Path, obj: dict) -> None:
    tmp=path.with_suffix(path.suffix+".pending")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    os.replace(tmp,path)


def load_tokenizer_helper(path: Path):
    spec=importlib.util.spec_from_file_location("exhaustive_colab_loader",path)
    if spec is None or spec.loader is None: raise RuntimeError(f"cannot import tokenizer helper: {path}")
    mod=importlib.util.module_from_spec(spec); sys.modules[spec.name]=mod; spec.loader.exec_module(mod)
    return mod


def iter_raw_jsonl(path: Path):
    with path.open("rb") as f:
        for n,raw in enumerate(f,1):
            body=raw.rstrip(b"\r\n")
            if not body.strip(): raise ValueError(f"blank JSONL row {n}")
            yield n,body


def read_jsonl(path: Path):
    for n,body in iter_raw_jsonl(path):
        row=json.loads(body.decode("utf-8"))
        if row.get("split") != "train": raise ValueError(f"non-train row at line {n}")
        yield row


def expected_manifest_rows(manifest: dict):
    cases=manifest.get("selected_cases_manifest")
    if not isinstance(cases,list): raise ValueError("manifest missing selected_cases_manifest row bindings")
    expected={}
    for case in cases:
        modes=case.get("rows")
        if not isinstance(modes,dict) or set(modes)!=MODES: raise ValueError("manifest case lacks exact four mode bindings")
        for info in modes.values():
            sid=info.get("sample_id"); digest=info.get("row_sha256")
            if not sid or not digest or sid in expected: raise ValueError("duplicate/missing manifest sample/hash binding")
            expected[sid]=digest
    if len(expected)!=int(manifest.get("selected_chat_rows",-1)):
        raise ValueError("manifest selected_chat_rows differs from row binding count")
    return expected


def tokenize_view(path: Path, helper, tokenizer, max_len: int, expected_hashes: dict[str,str]):
    rows=[]; ids=set(); cases={}
    for line_no,raw in iter_raw_jsonl(path):
        actual_hash=hashlib.sha256(raw).hexdigest()
        row=json.loads(raw.decode("utf-8"))
        if row.get("split") != "train": raise ValueError(f"non-train row at line {line_no}")
        sid=row.get("sample_id")
        if sid not in expected_hashes or expected_hashes[sid]!=actual_hash:
            raise ValueError(f"materialized row hash/sample binding mismatch at line {line_no}: {sid}")
        if not sid or sid in ids: raise ValueError(f"missing/duplicate sample_id: {sid}")
        ids.add(sid)
        encoded=helper.tokenize_assistant_only(row,tokenizer,max_sequence_tokens=max_len)
        if len(encoded["input_ids"]) != len(encoded["labels"]): raise ValueError("mask length mismatch")
        if not any(x != -100 for x in encoded["labels"]): raise ValueError(f"empty assistant target: {sid}")
        case=row.get("case_group_id")
        if case: cases.setdefault(case,set()).add(row.get("mode"))
        rows.append({"sample_id":sid,"case_group_id":case,"mode":row.get("mode"),"encoded":encoded})
    if not rows: raise ValueError("empty training view")
    if ids != set(expected_hashes): raise ValueError("materialized view sample IDs differ from selected manifest exact set")
    incomplete=[c for c,m in cases.items() if m != MODES]
    if incomplete: raise ValueError(f"view has incomplete modes for {len(incomplete)} cases")
    return rows


def make_length_batches(rows, micro: int, seed: int):
    """Shuffle bucket windows, then sort within each bounded window for dynamic padding."""
    order=list(range(len(rows))); rng=random.Random(seed); rng.shuffle(order)
    window=max(micro*32,128); batches=[]
    for start in range(0,len(order),window):
        chunk=order[start:start+window]
        chunk.sort(key=lambda i:len(rows[i]["encoded"]["input_ids"]))
        local=[chunk[i:i+micro] for i in range(0,len(chunk),micro)]
        rng.shuffle(local); batches.extend(local)
    return batches


def pad_collate(items, pad_id: int, device):
    import torch
    width=max(len(x["encoded"]["input_ids"]) for x in items)
    ids=[]; mask=[]; labels=[]
    for x in items:
        e=x["encoded"]; n=width-len(e["input_ids"])
        ids.append(e["input_ids"]+[pad_id]*n)
        mask.append(e["attention_mask"]+[0]*n)
        labels.append(e["labels"]+[-100]*n)
    return {"input_ids":torch.tensor(ids,dtype=torch.long,device=device),
            "attention_mask":torch.tensor(mask,dtype=torch.long,device=device),
            "labels":torch.tensor(labels,dtype=torch.long,device=device)}


def supervised_tokens(items):
    return sum(sum(t!=-100 for t in x["encoded"]["labels"]) for x in items)


def save_generation(model, tokenizer, out: Path, step: int, rows_done: int, cfg: dict, metrics: dict, optimizer=None, scaler=None, cursor=0):
    gen=out/f"generation_step_{step:06d}_rows_{rows_done:08d}"
    if gen.exists(): raise FileExistsError(gen)
    tmp=out/(gen.name+".pending")
    if tmp.exists(): shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    model.save_pretrained(tmp, safe_serialization=True)
    tokenizer.save_pretrained(tmp)
    atomic_json(tmp/"run_config.json",cfg)
    atomic_json(tmp/"metrics.json",metrics)
    import torch
    resume={"step":step,"rows_done":rows_done,"cursor_batches":cursor,"optimizer":optimizer.state_dict() if optimizer else None,"scaler":scaler.state_dict() if scaler else None,"cpu_rng":torch.get_rng_state(),"cuda_rng":torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []}
    torch.save(resume,tmp/"resume_state.pt")
    content={p.name:sha_file(p) for p in sorted(tmp.iterdir()) if p.is_file()}
    atomic_json(tmp/"generation_manifest.json",{"step":step,"rows_done":rows_done,"files":content,"complete":True})
    os.replace(tmp,gen)
    pointer={"generation":gen.name,"step":step,"rows_done":rows_done,"manifest_sha256":sha_file(gen/"generation_manifest.json")}
    atomic_json(out/"latest.json",pointer)
    return gen


def load_eval_fixtures(eval_path: Path):
    fixtures=[]
    with eval_path.open("r",encoding="utf-8") as f:
        for n,line in enumerate(f,1):
            if not line.strip(): raise ValueError(f"blank evaluation fixture {n}")
            x=json.loads(line)
            needed={"id","grade","mode","userproblem"}
            if not needed<=x.keys(): raise ValueError(f"eval fixture {n} lacks {sorted(needed-x.keys())}")
            fixtures.append(x)
    if len(fixtures)!=28: raise ValueError(f"expected 28 independent fixtures, got {len(fixtures)}")
    return fixtures


def generate_fixtures(model, tokenizer, fixtures, path: Path, stage: str, device):
    import torch
    system="Bạn là giáo viên hỗ trợ toán tiểu học Việt Nam. Dùng đúng dữ kiện, nói rõ vì sao chọn phép tính và đơn vị. Chỉ giải đầy đủ khi được yêu cầu. Khi xin gợi ý, chỉ hỗ trợ mức được yêu cầu, không đưa đáp số hay tính sẵn. Thiếu dữ kiện hoặc ảnh thì hỏi lại; không bịa kết quả quan sát hay lỗi thao tác."
    model.eval(); outputs=[]
    for x in fixtures:
        user=json.dumps({"grade":x["grade"],"problem":x["userproblem"],"mode":x["mode"]},ensure_ascii=False)
        messages=[{"role":"system","content":system},{"role":"user","content":user}]
        ids=tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,enable_thinking=False,return_tensors="pt").to(device)
        with torch.inference_mode():
            result=model.generate(input_ids=ids,attention_mask=torch.ones_like(ids),max_new_tokens=1536,do_sample=False,
              pad_token_id=tokenizer.pad_token_id,eos_token_id=tokenizer.eos_token_id)
        text=tokenizer.decode(result[0,ids.shape[1]:],skip_special_tokens=True)
        outputs.append({"stage":stage,"fixture_id":x["id"],"grade":x["grade"],"mode":x["mode"],"output":text,"max_new_tokens":1536,"possibly_truncated":bool(result.shape[1]-ids.shape[1]>=1536 and result[0,-1].item()!=tokenizer.eos_token_id)})
    model.train()
    temp=path.with_suffix(path.suffix+".pending")
    temp.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in outputs),encoding="utf-8")
    os.replace(temp,path)
    return outputs


def load_or_generate_base(model, tokenizer, fixtures, out: Path, fixture_sha: str, device):
    output=out/"base_generations.jsonl"; provenance=out/"base_generation_provenance.json"
    if output.exists() or provenance.exists():
        if not (output.exists() and provenance.exists()): raise ValueError("partial base-generation artifact; refuse reuse")
        p=json.loads(provenance.read_text(encoding="utf-8")) if provenance.exists() else None
        run_cfg=json.loads((out/"run_config.json").read_text(encoding="utf-8")) if (out/"run_config.json").exists() else {}
        lines=[json.loads(x) for x in output.read_text(encoding="utf-8").splitlines() if x.strip()]
        ids=[x.get("fixture_id") for x in lines]
        bound=(p.get("model")==MODEL and p.get("revision")==REVISION and p.get("fixture_sha256")==fixture_sha and p.get("base_untrained") is True and p.get("stage")=="base_before_training") if p else (run_cfg.get("model")==MODEL and run_cfg.get("revision")==REVISION and run_cfg.get("eval_fixtures_sha256")==fixture_sha)
        if (not bound or len(lines)!=28 or ids!=[x["id"] for x in fixtures] or any(x.get("stage")!="base_before_training" for x in lines)):
            raise ValueError("existing base outputs/config do not bind exactly to this model and fixture set")
        if p is None:
            p={"model":MODEL,"revision":REVISION,"fixture_sha256":fixture_sha,"count":28,"fixture_ids":ids,"stage":"base_before_training","base_untrained":True,"adapter_loaded":False,"provenance_reconstructed_from_matching_run_config":True}
            atomic_json(provenance,p)
        return lines, True
    outputs=generate_fixtures(model,tokenizer,fixtures,output,"base_before_training",device)
    atomic_json(provenance,{"model":MODEL,"revision":REVISION,"fixture_sha256":fixture_sha,"count":len(outputs),"fixture_ids":[x["id"] for x in fixtures],"stage":"base_before_training","base_untrained":True,"adapter_loaded":False})
    return outputs, False


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--train-view",required=True,type=Path)
    ap.add_argument("--eval-fixtures",required=True,type=Path)
    ap.add_argument("--tokenizer-helper",default="/content/mathvisionkid_full_text_training/code/exhaustive_colab_loader.py",type=Path)
    ap.add_argument("--budget-control",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--microbatch",type=int,choices=[1,2],default=1)
    ap.add_argument("--max-seq-len",type=int,default=2048)
    ap.add_argument("--seed",type=int,default=20261023)
    ap.add_argument("--checkpoint-every",type=int,default=100)
    ap.add_argument("--dry-run",action="store_true")
    ap.add_argument("--view-manifest",type=Path)
    ap.add_argument("--wait-view-until",type=float,default=None,help="Unix deadline to stop waiting for the verified selected view")
    args=ap.parse_args()
    control=json.loads(args.budget_control.read_text(encoding="utf-8"))
    control=control.get("budget",control)
    deadline=float(control["deadline_unix"]); now=time.time()
    if now>=deadline-RESERVE_SECONDS: raise TimeoutError("less than training reserve remains; refuse to start")
    args.out.mkdir(parents=True,exist_ok=True)
    cfg={"model":MODEL,"revision":REVISION,"quantization":"4bit NF4","bnb_4bit_use_double_quant":True,"compute_dtype":"float16","lora_r":16,"lora_alpha":16,"lora_dropout":0.0,"lora_bias":"none","target_modules":TARGET_MODULES,"gradient_checkpointing":"unsloth","optimizer":"bitsandbytes.optim.AdamW8bit","learning_rate":2e-4,"adam_betas":[0.9,0.999],"weight_decay":0.01,"scheduler":None,"loss_reduction":"ordinary_token_mean_per_microbatch","loss_aggregation":"microbatch_losses_weighted_by_example_count","microbatch":args.microbatch,"effective_batch":EFFECTIVE_BATCH,"grad_accumulation":EFFECTIVE_BATCH//args.microbatch,"packing":False,"flash_attention_2":False,"padding_free":False,"max_seq_len":args.max_seq_len,"seed":args.seed,"train_view_sha256":sha_file(args.train_view) if args.train_view.exists() else None,"eval_fixtures_sha256":sha_file(args.eval_fixtures),"evaluation_output_limit":1536,"base_cached_output_limit":512,"base_cached_outputs_all_eos_before_limit":True}
    atomic_json(args.out/"run_config.json",cfg)
    atomic_json(args.out/"progress.json",{"state":"RUNNER_STARTED_WAITING_FOR_GPU_PREFLIGHT","deadline_unix":deadline,"started_unix":time.time()})
    if args.dry_run:
        # Structural checks only; tokenizer import/tokenization requires the isolated venv.
        rows=list(read_jsonl(args.train_view)); fixtures=load_eval_fixtures(args.eval_fixtures)
        print(json.dumps({"state":"INPUTS_VALIDATED_DRY_RUN","train_rows":len(rows),"eval_fixtures":len(fixtures),"config":cfg},ensure_ascii=False)); return
    # Import Unsloth first: its patching must happen before Transformers/model imports.
    from unsloth import FastLanguageModel
    import torch
    if not torch.cuda.is_available(): raise RuntimeError("CUDA GPU unavailable")
    if not torch.cuda.get_device_name(0).lower().find("t4")>=0: raise RuntimeError("expected T4; refusing different GPU")
    if torch.cuda.is_bf16_supported(): raise RuntimeError("expected T4 FP16 path; BF16 unexpectedly reported")
    # Keep the base Python runtime untouched; caller must use the pinned venv executable.
    from transformers import BitsAndBytesConfig
    qconfig=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True)
    helper=load_tokenizer_helper(args.tokenizer_helper)
    model,tokenizer=FastLanguageModel.from_pretrained(model_name=MODEL,revision=REVISION,use_exact_model_name=True,max_seq_length=args.max_seq_len,dtype=torch.float16,load_in_4bit=True,quantization_config=qconfig,attn_implementation="sdpa")
    model=FastLanguageModel.get_peft_model(model,r=16,target_modules=TARGET_MODULES,lora_alpha=16,lora_dropout=0.0,bias="none",use_gradient_checkpointing="unsloth",random_state=args.seed,use_rslora=False,loftq_config=None)
    fixtures=load_eval_fixtures(args.eval_fixtures)
    base,base_reused=load_or_generate_base(model,tokenizer,fixtures,args.out,cfg["eval_fixtures_sha256"],torch.device("cuda"))
    atomic_json(args.out/"progress.json",{"state":"BASE_FIXTURES_READY_WAITING_FOR_VERIFIED_TRAIN_VIEW","base_outputs":len(base),"base_outputs_reused":base_reused,"deadline_unix":deadline})
    # The CPU sampler/materializer may still be running. Do not read or tokenize the view until
    # its adjacent manifest proves complete scan + exact selected-view materialization.
    view_manifest=args.view_manifest or args.train_view.with_name("training_view_manifest.json")
    wait_until=args.wait_view_until if args.wait_view_until is not None else deadline-2500
    while not (args.train_view.exists() and view_manifest.exists()):
        if time.time()>=wait_until: raise TimeoutError("selected training view/manifest did not arrive before wait deadline")
        time.sleep(min(10,max(1,wait_until-time.time())))
    manifest=json.loads(view_manifest.read_text(encoding="utf-8"))
    state=str(manifest.get("status",manifest.get("state",""))).upper()
    if any(x in state for x in ("FAIL","ERROR","TIMEOUT")): raise ValueError(f"sampler/materializer did not pass: {state}")
    scan_flags=[manifest[k] for k in ("all_scanned","all_rows_scanned","all_members_scanned","scan_complete") if k in manifest]
    exact_scan=(manifest.get('members_complete')==32 and manifest.get('raw_train_rows_scanned')==6502344 and manifest.get('recipe_sha256')=='1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8')
    if not exact_scan and (not scan_flags or not all(v is True for v in scan_flags)): raise ValueError("manifest lacks positive all-scanned completion evidence")
    if manifest.get("all_four_modes_preserved") is not True: raise ValueError("manifest does not confirm all four modes")
    if manifest.get("training_view_sha256") and manifest["training_view_sha256"]!=sha_file(args.train_view):
        raise ValueError("materialized training view SHA256 differs from signed-by-content manifest")
    expected_hashes=expected_manifest_rows(manifest)
    rows=tokenize_view(args.train_view,helper,tokenizer,args.max_seq_len,expected_hashes)
    declared=int(manifest.get("selected_chat_rows",manifest.get("selected_rows",-1)))
    if declared!=len(rows): raise ValueError(f"manifest selected row count {declared} != materialized view rows {len(rows)}")
    cfg["train_view_sha256"]=sha_file(args.train_view); cfg["train_view_manifest_sha256"]=sha_file(view_manifest); cfg["view_rows"]=len(rows)
    atomic_json(args.out/"run_config.json",cfg)
    import bitsandbytes as bnb
    optimizer=bnb.optim.AdamW8bit([p for p in model.parameters() if p.requires_grad],lr=2e-4,betas=(0.9,0.999),weight_decay=0.01)
    scaler=torch.amp.GradScaler("cuda",enabled=True,init_scale=1024.0)
    device=torch.device("cuda"); pad_id=tokenizer.pad_token_id or 151643
    # Choose the exact same 16 length-quantile rows for both physical microbatches.
    sorted_rows=sorted(rows,key=lambda x:len(x["encoded"]["input_ids"]))
    bench_rows=[sorted_rows[round(i*(len(sorted_rows)-1)/15)] for i in range(16)]
    bench_rng_cpu=torch.get_rng_state(); bench_rng_cuda=torch.cuda.get_rng_state_all(); timings={}
    for micro in (1,2):
        reps=[]; peaks=[]; failures=[]
        accum=EFFECTIVE_BATCH//micro
        for rep in range(3):
            torch.set_rng_state(bench_rng_cpu); torch.cuda.set_rng_state_all(bench_rng_cuda)
            optimizer.zero_grad(set_to_none=True)
            try:
                model.train()
                # First identical complete forward/backward pass is warm-up; no optimizer step occurs.
                for i in range(0,16,micro):
                    items=bench_rows[i:i+micro]; batch=pad_collate(items,pad_id,device)
                    with torch.autocast("cuda",dtype=torch.float16): loss=model(**batch).loss/accum
                    scaler.scale(loss).backward()
                optimizer.zero_grad(set_to_none=True); torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
                t0=time.monotonic(); nonpad=supervised=0
                for i in range(0,16,micro):
                    items=bench_rows[i:i+micro]; batch=pad_collate(items,pad_id,device)
                    with torch.autocast("cuda",dtype=torch.float16): loss=model(**batch).loss/accum
                    scaler.scale(loss).backward()
                    nonpad+=int(batch["attention_mask"].sum().item()); supervised+=supervised_tokens(items)
                torch.cuda.synchronize(); seconds=max(time.monotonic()-t0,1e-9)
                reps.append({"seconds":seconds,"nonpad_tokens":nonpad,"supervised_tokens":supervised,"unique_examples":16})
                peaks.append(torch.cuda.max_memory_allocated()); optimizer.zero_grad(set_to_none=True)
            except torch.cuda.OutOfMemoryError:
                failures.append("OOM"); optimizer.zero_grad(set_to_none=True); torch.cuda.empty_cache(); break
            finally:
                optimizer.zero_grad(set_to_none=True)
        if reps and not failures:
            mean_seconds=sum(x["seconds"] for x in reps)/len(reps)
            timings[str(micro)]={"state":"PASS","repeats":reps,"mean_group_seconds":mean_seconds,"unique_examples_per_second":16/mean_seconds,"nonpad_tokens_per_second":sum(x["nonpad_tokens"] for x in reps)/sum(x["seconds"] for x in reps),"supervised_tokens_per_second":sum(x["supervised_tokens"] for x in reps)/sum(x["seconds"] for x in reps),"peak_vram_bytes":max(peaks),"optimizer_steps_during_probe":0,"same_16_examples":True}
        else:
            timings[str(micro)]={"state":"OOM" if failures else "BENCHMARK_FAILED","repeats":reps,"mean_group_seconds":None,"unique_examples_per_second":0,"nonpad_tokens_per_second":0,"supervised_tokens_per_second":0,"peak_vram_bytes":max(peaks,default=0),"optimizer_steps_during_probe":0,"same_16_examples":True}
    torch.set_rng_state(bench_rng_cpu); torch.cuda.set_rng_state_all(bench_rng_cuda)
    if timings["1"]["state"]!="PASS": raise RuntimeError("microbatch-1 forward/backward benchmark failed; no safe config")
    usable=[m for m in (1,2) if timings[str(m)]["state"]=="PASS"]
    micro=min(usable,key=lambda m:timings[str(m)]["mean_group_seconds"])
    cfg["selected_microbatch"]=micro; cfg["benchmark"]=timings; cfg["grad_accumulation"]=EFFECTIVE_BATCH//micro
    atomic_json(args.out/"run_config.json",cfg)
    measured_at_unix=time.time()
    measured_remaining_seconds=max(0.0,deadline-measured_at_unix)
    target_steps=(int((measured_remaining_seconds-RESERVE_SECONDS)/(timings[str(micro)]["mean_group_seconds"]*1.35)))
    if target_steps<1: raise TimeoutError("measured throughput leaves no optimizer step before export reserve")
    cfg.update(measured_at_unix=measured_at_unix,measured_remaining_seconds=measured_remaining_seconds,
               checkpoint_export_reserve_seconds=RESERVE_SECONDS,safety_factor=1.35,
               measured_group_seconds=timings[str(micro)]["mean_group_seconds"],target_steps=target_steps,
               deadline_unix=deadline)
    atomic_json(args.out/"run_config.json",cfg)
    step=rows_done=cursor=0; total_loss=0.0; successful_examples=successful_sup=successful_nonpadding=0; successful_unique_ids=set(); start_time=time.time(); last_group_loss=None
    ids_log=args.out/"successful_ids.jsonl"
    if not ids_log.exists(): ids_log.touch()
    batches_per_epoch=math.ceil(len(rows)/micro)
    accumulation=EFFECTIVE_BATCH//micro
    base_batches=make_length_batches(rows,micro,args.seed)
    batches=[]; epoch_seed=0
    while len(batches)<target_steps*accumulation:
        batches.extend(make_length_batches(rows,micro,args.seed+epoch_seed)); epoch_seed+=1
    optimizer.zero_grad(set_to_none=True)
    for group_start in range(0,len(batches),accumulation):
        if step>=target_steps or time.time()>=deadline-RESERVE_SECONDS: break
        group=batches[group_start:group_start+accumulation]
        if not group: break
        rng_cpu=torch.get_rng_state(); rng_cuda=torch.cuda.get_rng_state_all(); retry=0
        while True:
            optimizer.zero_grad(set_to_none=True); group_loss=0.; group_nonpadding=0; group_supervised=0; failed=False
            group_rows=sum(len(bix) for bix in group)
            for bix in group:
                items=[rows[i] for i in bix]; batch=pad_collate(items,pad_id,device)
                with torch.autocast("cuda",dtype=torch.float16): out=model(**batch); loss=out.loss*(len(items)/group_rows)
                if not torch.isfinite(loss): failed=True; break
                scaler.scale(loss).backward(); group_loss+=float(loss.detach())
                group_nonpadding+=int(batch["attention_mask"].sum().item())
                group_supervised+=supervised_tokens(items)
            if not failed:
                scaler.unscale_(optimizer)
                grads=[p.grad for p in model.parameters() if p.grad is not None]
                if grads and all(torch.isfinite(g).all().item() for g in grads):
                    torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad],1.0)
                    oldscale=scaler.get_scale(); scaler.step(optimizer); scaler.update()
                    if scaler.get_scale()>=oldscale:
                        step+=1; total_loss+=group_loss; last_group_loss=group_loss
                        step_ids=[rows[i]["sample_id"] for b in group for i in b]
                        successful_examples+=len(step_ids); successful_unique_ids.update(step_ids)
                        successful_sup+=group_supervised; successful_nonpadding+=group_nonpadding; cursor=group_start+len(group)
                        with ids_log.open("a",encoding="utf-8") as f:
                            f.write("".join(json.dumps({"step":step,"sample_id":sid},ensure_ascii=False)+"\n" for sid in step_ids)); f.flush(); os.fsync(f.fileno())
                        break
            retry+=1
            if retry>3: raise FloatingPointError("AMP/non-finite group failed after three same-batch retries")
            scaler.update(new_scale=max(1.0,scaler.get_scale()/2)); torch.set_rng_state(rng_cpu); torch.cuda.set_rng_state_all(rng_cuda)
        if step%10==0:
            grads=[p.grad for p in model.parameters() if p.grad is not None]
            gradients_finite=bool(grads) and all(bool(torch.isfinite(g).all().item()) for g in grads)
            atomic_json(args.out/"progress.json",{"state":"TRAINING","step":step,"rows_done":successful_examples,"supervised_tokens":successful_sup,"nonpadding_tokens":successful_nonpadding,"cursor_batches":cursor,"deadline_unix":deadline,"elapsed_seconds":time.time()-start_time,"current_loss":last_group_loss,"scaler_scale":float(scaler.get_scale()),"gradients_finite_after_optimizer_step":gradients_finite,"overflow_retries":retry})
        if step%args.checkpoint_every==0:
            elapsed=time.time()-start_time
            metrics={"step":step,"rows_done":successful_examples,"supervised_tokens":successful_sup,"nonpadding_tokens":successful_nonpadding,"mean_loss":total_loss/max(step,1),"last_group_loss":last_group_loss,"elapsed_seconds":elapsed,"rows_per_second":successful_examples/max(elapsed,1e-9),"unique_examples":len(successful_unique_ids),"unique_examples_per_second":len(successful_unique_ids)/max(elapsed,1e-9),"example_exposures_per_second":successful_examples/max(elapsed,1e-9),"supervised_tokens_per_second":successful_sup/max(elapsed,1e-9),"nonpadding_tokens_per_second":successful_nonpadding/max(elapsed,1e-9),"peak_vram_bytes":torch.cuda.max_memory_allocated(),"input_cursor_batches":cursor,"completed_view_epochs":successful_examples/len(rows),"view_fraction_complete":(successful_examples%len(rows))/len(rows)}
            save_started=time.monotonic(); gen_path=save_generation(model,tokenizer,args.out,step,successful_examples,cfg,metrics,optimizer,scaler,cursor); save_elapsed=time.monotonic()-save_started
            timing_path=args.out/"checkpoint_timing.jsonl"
            with timing_path.open("a",encoding="utf-8") as f:
                f.write(json.dumps({"step":step,"rows_done":successful_examples,"generation":gen_path.name,"save_seconds":save_elapsed,"measured_utc":datetime.now(timezone.utc).isoformat()},ensure_ascii=False)+"\n"); f.flush(); os.fsync(f.fileno())
    # Save final adapter and tokenizer before export deadline; retain exact subset/step claims.
    elapsed=time.time()-start_time
    metrics={"step":step,"rows_done":successful_examples,"supervised_tokens":successful_sup,"nonpadding_tokens":successful_nonpadding,"mean_loss":total_loss/max(step,1),"last_group_loss":last_group_loss,"elapsed_seconds":elapsed,"rows_per_second":successful_examples/max(elapsed,1e-9),"unique_examples":len(successful_unique_ids),"unique_examples_per_second":len(successful_unique_ids)/max(elapsed,1e-9),"example_exposures_per_second":successful_examples/max(elapsed,1e-9),"supervised_tokens_per_second":successful_sup/max(elapsed,1e-9),"nonpadding_tokens_per_second":successful_nonpadding/max(elapsed,1e-9),"peak_vram_bytes":torch.cuda.max_memory_allocated(),"input_cursor_batches":cursor,"completed_view_epochs":successful_examples/len(rows),"view_fraction_complete":(successful_examples%len(rows))/len(rows),"stop_reason":"deadline_reserve_or_measured_max_steps"}
    prior=json.loads((args.out/"latest.json").read_text(encoding="utf-8")) if (args.out/"latest.json").exists() else None
    if not prior or prior.get("step")!=step or prior.get("rows_done")!=successful_examples:
        save_started=time.monotonic(); gen_path=save_generation(model,tokenizer,args.out,step,successful_examples,cfg,metrics,optimizer,scaler,cursor); save_elapsed=time.monotonic()-save_started
        timing_path=args.out/"checkpoint_timing.jsonl"
        with timing_path.open("a",encoding="utf-8") as f:
            f.write(json.dumps({"step":step,"rows_done":successful_examples,"generation":gen_path.name,"save_seconds":save_elapsed,"measured_utc":datetime.now(timezone.utc).isoformat()},ensure_ascii=False)+"\n"); f.flush(); os.fsync(f.fileno())
    after=generate_fixtures(model,tokenizer,fixtures,args.out/"adapter_generations.jsonl","adapter_after_training",device)
    with zipfile.ZipFile(args.out/"adapter_export.zip.pending","w",zipfile.ZIP_DEFLATED) as z:
        gen=json.loads((args.out/"latest.json").read_text())["generation"]
        for p in sorted((args.out/gen).iterdir()):
            if p.is_file() and p.name!="resume_state.pt": z.write(p,arcname=p.name)
    os.replace(args.out/"adapter_export.zip.pending",args.out/"adapter_export.zip")
    atomic_json(args.out/"run_complete.json",{"complete":True,"step":step,"rows_done":successful_examples,"eval_fixture_count":len(fixtures),"base_outputs":len(base),"adapter_outputs":len(after),"adapter_zip_sha256":sha_file(args.out/"adapter_export.zip"),"metrics":metrics,"config":cfg})
    print(json.dumps({"state":"COMPLETE","step":step,"rows_done":successful_examples,"zip_sha256":sha_file(args.out/"adapter_export.zip")},ensure_ascii=False))

if __name__=="__main__": main()
