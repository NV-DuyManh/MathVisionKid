import sys,inspect,re,json,time
sampler_module=sys.modules['mvk_colab_train_view_worker']
_original_verified_member_lines=sampler_module._iter_member_lines
_first_key_id=re.compile(rb'^\s*\{\s*"sample_id"\s*:\s*"([A-Za-z0-9_:\-./]+)"')
selected_row_readback_overlay={'state':'ACTIVE','first_pass_changed':False,'full_archive_hash_validation_preserved':True,'selected_full_row_hash_validation_preserved':True,'unselected_first_key_ids_skipped':0,'fallback_full_parser_lines':0,'applied_unix':time.time()}
def _verified_selected_member_lines(archive_path,member):
    frame=inspect.currentframe().f_back
    selected=frame.f_locals.get('selected_rows') if frame else None
    wanted={info['sample_id'].encode() for modes in selected.values() for info in modes.values()} if selected else None
    del frame
    for line in _original_verified_member_lines(archive_path,member):
        if wanted is not None:
            match=_first_key_id.match(line)
            if match and match.group(1) not in wanted:
                selected_row_readback_overlay['unselected_first_key_ids_skipped']+=1
                continue
            if match is None:selected_row_readback_overlay['fallback_full_parser_lines']+=1
        yield line
sampler_module._iter_member_lines=_verified_selected_member_lines
(budget_root/'sampling/selected_row_readback_overlay.json').write_text(json.dumps(selected_row_readback_overlay,indent=2))
print(json.dumps(selected_row_readback_overlay))
