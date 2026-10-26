#!/usr/bin/env python3
"""Fail-closed final quality report builder for the three-hour T4 experiment.
Consumes normalized final run and publication evidence plus existing runtime receipts.
It never estimates missing model/quality statistics or asserts deployment readiness.
"""
from __future__ import annotations
import argparse, json, math, os, time
from pathlib import Path

START_UTC="2026-10-23T14:15:52.441626+00:00"
DEADLINE_UTC="2026-10-23T17:15:52.441626+00:00"
EXPECTED={"corpus_source_versions":1629906,"historical_corpus_source_versions":1629922,"train_rows":6502344,"validation_rows":24,"test_rows":24,"view_cases":4000,"view_chat_rows":16000,"eval_fixtures":28,"model_revision":"70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"}
REQUIRED_RUN=("state","model","revision","framework_versions","training_configuration","view_cases","view_chat_rows","successful_optimizer_steps","example_exposures","unique_examples","supervised_tokens","nonpad_tokens","completed_view_epochs","peak_vram_bytes","adapter_zip_sha256","base_fixture_count","adapter_fixture_count","base_review","adapter_review")
REQUIRED_12=("experiment_scope","data_lineage_and_splits","selected_training_view","model_and_runtime","training_configuration","throughput_benchmarks","actual_training_progress","base_vs_adapter_evaluation","semantic_quality_by_mode","grade_fit_and_known_gaps","artifact_publication_status","limitations_and_readiness")


def read_json(path):
 p=Path(path)
 if not p.exists():raise FileNotFoundError(f"required evidence missing: {p}")
 d=json.loads(p.read_text(encoding="utf-8-sig"))
 # Unwrap known tool receipts by decoding JSON strings in output text.
 for _ in range(8):
  if isinstance(d,dict) and "outputs" in d and isinstance(d["outputs"],list):
   got=None
   for o in d["outputs"]:
    if isinstance(o,dict):
     for t in o.get("text",[]):
      if isinstance(t,str):
       try:got=json.loads(t);break
       except Exception:pass
    if got is not None:break
   if got is None:break
   d=got;continue
  if isinstance(d,dict) and "result" in d and isinstance(d["result"],dict):d=d["result"];continue
  break
 return d


def need(obj,key,path):
 if key not in obj or obj[key] is None:raise ValueError(f"missing required field {path}.{key}")
 return obj[key]


def review_summary(review,label):
 if review.get("fixture_count")!=28 or review.get("all_fixture_ids_matched") is not True:raise ValueError(f"{label} semantic review must cover all 28 exact fixture IDs")
 summary=need(review,"mathematical_behavior_strict_summary",label)
 per=need(summary,"per_mode",label)
 expected_modes={"answer":13,"hint_no_answer":5,"student_error":4,"missing_or_contradictory_info":6}
 result={}
 for mode,count in expected_modes.items():
  rec=need(per,mode,f"{label}.per_mode")
  if rec.get("denominator")!=count or rec.get("fixture_count")!=count:raise ValueError(f"{label}/{mode} denominator mismatch")
  passed=need(rec,"strict_mathematical_behavior_pass",f"{label}.{mode}")
  result[mode]={"pass":passed,"denominator":count,"pass_rate":passed/count}
 return result


def build(args):
 budget=read_json(args.budget_status)
 if isinstance(budget,dict) and isinstance(budget.get("budget"),dict):budget=budget["budget"]
 started=need(budget,"started_utc","budget");deadline=need(budget,"deadline_utc","budget")
 if started!=START_UTC or deadline!=DEADLINE_UTC:raise ValueError("budget UTC bounds differ from authorized window")
 summary=read_json(args.sampling_summary)
 # Caller may supply either the sampler manifest directly or receipt containing its manifest object.
 manifest=summary.get("manifest",summary.get("sampling_manifest",summary))
 for k,v in (("raw_train_rows_scanned",EXPECTED["train_rows"]),("selected_cases",EXPECTED["view_cases"]),("selected_chat_rows",EXPECTED["view_chat_rows"]),("all_four_modes_preserved",True)):
  if manifest.get(k)!=v:raise ValueError(f"sampling summary {k} mismatch/missing; got {manifest.get(k)!r}")
 if manifest.get("recipe_sha256") is None or manifest.get("training_view_sha256") is None:raise ValueError("sampling summary lacks recipe/view SHA")
 run=read_json(args.run_complete)
 for k in REQUIRED_RUN:need(run,k,"run_complete")
 if run["state"] not in ("COMPLETE","COMPLETE_WITH_LIMITATIONS"):raise ValueError("run is not complete")
 if run["model"]!="Qwen/Qwen3-1.7B" or run["revision"]!=EXPECTED["model_revision"]:raise ValueError("wrong model identity/revision")
 if run["view_cases"]!=EXPECTED["view_cases"] or run["view_chat_rows"]!=EXPECTED["view_chat_rows"]:raise ValueError("actual run view counts mismatch")
 if run["base_fixture_count"]!=28 or run["adapter_fixture_count"]!=28:raise ValueError("both base and adapter outputs must cover 28 fixtures")
 base=review_summary(read_json(args.base_review),"base_review")
 adapter=review_summary(read_json(args.adapter_review),"adapter_review")
 publication=read_json(args.publication_proof)
 for k in ("artifact_name","sha256","bytes","fresh_raw_readback_verified"):need(publication,k,"publication_proof")
 if publication["fresh_raw_readback_verified"] is not True or publication["sha256"]!=run["adapter_zip_sha256"]:raise ValueError("published artifact does not have matching fresh raw readback SHA")
 bench=read_json(args.benchmarks)
 base_bench=need(bench,"torch_baseline","benchmarks"); uns=need(bench,"unsloth","benchmarks")
 expected_ids=run.get("benchmark_sample_ids")
 if not expected_ids or base_bench.get("sample_ids")!=expected_ids or uns.get("sample_ids")!=expected_ids:raise ValueError("benchmark sample IDs not equal/missing")
 if base_bench.get("optimizer_steps")!=0 or uns.get("optimizer_steps")!=0:raise ValueError("benchmark must be optimizer-free")
 before=base["answer"];after=adapter["answer"]
 regressions={m:{"base":base[m],"adapter":adapter[m]} for m in base if adapter[m]["pass_rate"]<base[m]["pass_rate"]}
 if run.get("finish_utc") is None:raise ValueError("missing actual finish timestamp")
 training_elapsed=need(run,"elapsed_seconds","run_complete")
 if not isinstance(training_elapsed,(float,int)) or training_elapsed<=0:raise ValueError("invalid actual training elapsed time")
 finish_unix=need(run,"finish_unix","run_complete")
 start_unix=need(budget,"started_unix","budget");deadline_unix=need(budget,"deadline_unix","budget")
 wallclock_seconds=finish_unix-start_unix
 if wallclock_seconds<=0:raise ValueError("actual finish precedes experiment budget start")
 package=read_json(args.package_proof) if args.package_proof else {"provided":False,"status":"NOT_PROVIDED"}
 checkpoint=read_json(args.checkpoint_proof) if args.checkpoint_proof else run.get("checkpoint_publication",run.get("checkpoint_proof",{"provided":False,"status":"NOT_PROVIDED_IN_RUN_RECORD"}))
 if package.get("fresh_raw_readback_verified") is not True:package_status="NOT_VERIFIED"
 else:package_status="FRESH_READBACK_VERIFIED"
 fields={
  "experiment_scope":{"type":"new stratified-view QLoRA benchmark; not a full-corpus epoch","budget_started_utc":started,"deadline_utc":deadline,"finish_utc":run["finish_utc"],"finish_time_source":run.get("finish_time_source","normalized run record"),"wallclock_seconds_from_budget_start":wallclock_seconds,"training_elapsed_seconds":training_elapsed,"within_deadline":finish_unix<=deadline_unix},
  "data_lineage_and_splits":{"source_versions":EXPECTED["corpus_source_versions"],"historical_source_versions":EXPECTED["historical_corpus_source_versions"],"historical_delta_preserved":16,"train_rows":EXPECTED["train_rows"],"validation_rows":EXPECTED["validation_rows"],"test_rows":EXPECTED["test_rows"],"validation_test_training_access":False,"recipe_sha256":manifest["recipe_sha256"],"unique_examples_trained":run["unique_examples"],"train_rows_remaining_by_unique_id":EXPECTED["train_rows"]-run["unique_examples"],"train_rows_outside_selected_view":EXPECTED["train_rows"]-EXPECTED["view_chat_rows"],"unique_examples_remaining_in_selected_view":EXPECTED["view_chat_rows"]-run["unique_examples"],"remainder_note":"Remainders are derived from distinct sample IDs, not optimizer exposures."},
  "selected_training_view":{"cases":run["view_cases"],"chat_rows":run["view_chat_rows"],"view_sha256":manifest["training_view_sha256"],"all_four_modes":True,"sampling_scope":"deterministic skill-stratified subset"},
  "model_and_runtime":{"model":run["model"],"revision":run["revision"],"framework_versions":run["framework_versions"],"gpu":run.get("gpu"),"peak_vram_bytes":run["peak_vram_bytes"]},
  "training_configuration":need(run,"training_configuration","run_complete"),
  "throughput_benchmarks":{"native_torch":base_bench,"unsloth":uns,"same_16_ids":expected_ids,"sample_id_evidence":bench.get("sample_id_evidence"),"posthoc_reconstruction":bench.get("posthoc_reconstruction"),"comparability_note":"native Transformers causal-LM cross-entropy is not the earlier V3 selected-logit sparse kernel; Unsloth IDs are post-hoc reconstructed when original worker omitted them; compare only as reported, no quality implication"},
  "actual_training_progress":{"successful_optimizer_steps":run["successful_optimizer_steps"],"example_exposures":run["example_exposures"],"unique_examples":run["unique_examples"],"supervised_tokens":run["supervised_tokens"],"nonpad_tokens":run["nonpad_tokens"],"completed_view_epochs":run["completed_view_epochs"],"mean_loss":run.get("mean_loss"),"peak_vram_bytes":run["peak_vram_bytes"]},
  "base_vs_adapter_evaluation":{"base_outputs":28,"adapter_outputs":28,"base_truncation_count":run.get("base_truncation_count"),"adapter_truncation_count":run.get("adapter_truncation_count"),"generation":{"fixture_count":28,"decoding":"greedy (do_sample=false)","enable_thinking":False,"explicit_thinking_reasoning_process_benchmarked":False,"base_max_new_tokens":need(run["training_configuration"],"base_cached_output_limit","training_configuration"),"adapter_max_new_tokens":need(run["training_configuration"],"evaluation_output_limit","training_configuration"),"truncation_is_counted_as_failure":True,"base_outputs_all_eos_before_limit":run["training_configuration"].get("base_cached_outputs_all_eos_before_limit")},"semantic_comparison_only":True,"limitation":"This is a small fixed 28-fixture greedy comparison, not an explicit chain-of-thought or reasoning-process benchmark."},
  "semantic_quality_by_mode":{"base":base,"adapter":adapter,"regressions":regressions,"strict_all_modes_improved":len(regressions)==0 and all(adapter[m]["pass_rate"]>base[m]["pass_rate"] for m in base)},
  "grade_fit_and_known_gaps":{"base":read_json(args.base_review).get("mathematical_behavior_strict_summary",{}).get("gradefit_reported_separately"),"adapter":read_json(args.adapter_review).get("mathematical_behavior_strict_summary",{}).get("gradefit_reported_separately"),"known_grade3_fraction_decimal_fit_limitation":"report as reviewer provided; no grade changes after seeing outputs"},
  "artifact_publication_status":{"adapter_zip_sha256":run["adapter_zip_sha256"],"publication":{"receipt":publication,"evidence_scope":"fresh raw-byte readback of the published adapter ZIP only","fresh_raw_readback_verified":True},"checkpoint_save_evidence":checkpoint,"checkpoint_scope_note":"Checkpoint evidence is reported separately from adapter ZIP publication; only the specific receipt’s save/readback claim is in scope.","final_package_verification":package_status,"package_proof":package,"drive_scope_note":"The reported readback applies only to the specifically identified artifact in the receipt; it does not imply verification of unrelated Drive objects."},
  "limitations_and_readiness":{"production_approved":False,"release_recommendation":"evaluation-only / internal experiment; production approval requires separate review","scanned_metadata_is_semantic_QA":False,"no_full_epoch_claim":True,"base_512_cap_truncation_is_scored_as_failure":True,"quality_status":"IMPROVED_ALL_MODES" if not regressions and all(adapter[m]["pass_rate"]>base[m]["pass_rate"] for m in base) else ("REGRESSION_OR_NO_IMPROVEMENT" if regressions or any(adapter[m]["pass_rate"]<=base[m]["pass_rate"] for m in base) else "INCOMPLETE"),"recommendation_rule":"Any per-mode regression or no improvement means retain as experiment only and do not recommend promotion; even improvement across all modes does not constitute production approval.","quality_based_recommendation":"retain as experiment only; do not promote because of per-mode regression or absent improvement" if regressions or any(adapter[m]["pass_rate"]<=base[m]["pass_rate"] for m in base) else "internal experiment only; any production proposal requires a separate review"}
 }
 if set(fields)!=set(REQUIRED_12):raise AssertionError("internal 12-field contract mismatch")
 report={"schema":"MathVisionKid.t4_final_quality_report.v1","status":"EVIDENCE_COMPLETE","status_meaning":"Required evidence validated and report constructed; this is not a model-quality pass or production approval.","required_field_count":12,"required_fields":list(REQUIRED_12),"fields":fields,"generated_unix":time.time()}
 args.output.parent.mkdir(parents=True,exist_ok=True)
 atomic=args.output.with_suffix(args.output.suffix+".pending");atomic.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8");os.replace(atomic,args.output)
 lines=["# Báo cáo chất lượng cuối kỳ — thử nghiệm Qwen3-1.7B trên T4",""]
 titles={"experiment_scope":"Phạm vi và thời hạn","data_lineage_and_splits":"Nguồn dữ liệu và chia tập","selected_training_view":"Tập huấn luyện được chọn","model_and_runtime":"Mô hình và môi trường","training_configuration":"Cấu hình huấn luyện","throughput_benchmarks":"Benchmark tốc độ","actual_training_progress":"Tiến độ thực tế","base_vs_adapter_evaluation":"So sánh đầu ra base và adapter","semantic_quality_by_mode":"Chất lượng theo chế độ","grade_fit_and_known_gaps":"Mức phù hợp lớp và giới hạn","artifact_publication_status":"Trạng thái xuất bản adapter","limitations_and_readiness":"Giới hạn và mức sẵn sàng"}
 for key in REQUIRED_12:
  value=fields[key]
  lines.extend([f"## {titles[key]}","", "```json",json.dumps(value,ensure_ascii=False,indent=2),"```",""])
 tmp=args.markdown.with_suffix(args.markdown.suffix+".pending");tmp.write_text("\n".join(lines),encoding="utf-8");os.replace(tmp,args.markdown)
 return report


def main():
 p=argparse.ArgumentParser();p.add_argument('--budget-status',type=Path,required=True);p.add_argument('--sampling-summary',type=Path,required=True);p.add_argument('--run-complete',type=Path,required=True);p.add_argument('--base-review',type=Path,required=True);p.add_argument('--adapter-review',type=Path,required=True);p.add_argument('--benchmarks',type=Path,required=True);p.add_argument('--publication-proof',type=Path,required=True);p.add_argument('--package-proof',type=Path);p.add_argument('--checkpoint-proof',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--markdown',type=Path,required=True);a=p.parse_args();r=build(a);print(json.dumps({'status':r['status'],'output':str(a.output),'markdown':str(a.markdown)},ensure_ascii=False))
if __name__=='__main__':main()
