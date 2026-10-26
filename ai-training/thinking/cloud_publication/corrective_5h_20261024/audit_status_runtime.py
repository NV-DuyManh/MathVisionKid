import json,pathlib
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
p=root5/'selected_view_tokenization_audit.json'
out={'audit_process_exit':corrective_audit_process.poll() if globals().get('corrective_audit_process') else None,'report_exists':p.exists()}
if p.exists():
 d=json.loads(p.read_bytes());out['report']={k:v for k,v in d.items() if k not in ['input_length_histogram_by_mode','completion_length_histogram_by_mode','prompt_examples','supplied_student_work_examples','duplicate_assistant_templates']};out['duplicate_template_summary']={k:v for k,v in d.get('duplicate_assistant_templates',{}).items() if k!='top20'}
out['audit_log_tail']=(root5/'audit.log').read_text(errors='replace')[-2500:]
print(json.dumps(out,ensure_ascii=False))
