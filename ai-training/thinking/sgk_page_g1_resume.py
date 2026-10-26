"""Record only pages actually viewed in the replacement G1 audit turn."""
import hashlib, json
from pathlib import Path

RUN=Path(__file__).parent/'cloud_publication/sgk_page_audit_20261019'
OUT=RUN/'g1v2_audit'
SPECS={
88: (['successor_predecessor_sequence','threshold_selection','attribute_filtered_extrema'], ['G1V2_ATTRIBUTE_FILTERED_EXTREMA']),
89: (['transfer_between_two_groups','temporal_stage_order','duplicate_score_assignment'], ['G1V2_TRANSFER_COMPARISON','G1V2_TEMPORAL_STAGE_ORDER','G1V2_DUPLICATE_SCORE_ASSIGNMENT']),
90: (['expression_target_classification','bin_occupancy_count','sum_pyramid'], []),
91: (['expression_comparison','expression_group_frequency_table'], []),
92: (['seven_segment_digit_construction','fixed_match_count_digit_selection'], ['G1V2_MATCHSTICK_DIGIT_ASSET']),
93: (['single_match_move_equation_repair','two_stage_gate_pair_sum_path'], ['G1V2_SINGLE_MATCH_EQUATION_REPAIR','G1V2_GATE_PAIR_SUM_PATH']),
94: (['bundled_tens_units','number_read_write'], []),
95: (['tens_units_decomposition','labelled_length_extrema','two_digit_card_enumeration_no_leading_zero'], ['G1V2_TWO_DIGIT_NUMBER_CARD_CONSTRUCTION']),
96: (['round_tens_arithmetic','no_carry_column_arithmetic','equal_expression_matching'], []),
97: (['sequential_arithmetic_network','arithmetic_result_table'], ['G1V2_LINKED_ARITHMETIC_NETWORK']),
98: (['multi_blank_column_addition_subtraction','expression_threshold_filter'], ['G1V2_MISSING_DIGITS_COLUMN_SUBTRACTION']),
99: (['part_whole_subtraction','join_two_disjoint_groups'], []),
100: (['cube_cuboid_identification_under_rotation','composite_picture_shape_inventory'], ['G1V2_COMPOSITE_SHAPE_INVENTORY_ASSET']),
101: (['matchstick_remove_edges_count_triangles','periodic_shape_and_solid_attributes'], ['G1V2_REMOVE_MATCHES_TRIANGLE_COUNT_ASSET']),
102: (['activity_clock_matching','calendar_anchor_day_offset','yesterday_tomorrow'], ['G1V2_CLOCK_READING_IMAGE_ASSET','G1V2_CALENDAR_ANCHOR_OFFSET']),
103: (['physical_centimetre_measurement','grid_reference_length_comparison','plausible_unit_reference_estimation'], ['G1V2_DIRECT_LENGTH_IMAGE_ASSET','G1V2_COMMON_REFERENCE_LENGTH_COMPARISON','G1V2_PLAUSIBLE_REFERENCE_ESTIMATION']),
104: (['number_word_matching','ascending_sort','column_arithmetic','analogue_clock_reading'], ['G1V2_CLOCK_READING_IMAGE_ASSET']),
105: (['join_and_remove_word_problems','weekday_to_date_offset','physical_ruler_measurement','composite_square_count'], ['G1V2_CALENDAR_ANCHOR_OFFSET','G1V2_DIRECT_LENGTH_IMAGE_ASSET','G1V2_COMPOSITE_SQUARE_COUNT_ASSET']),
}

def main():
    old=[json.loads(x) for x in (OUT/'page_review.jsonl').read_text(encoding='utf-8').splitlines()]
    seen={r['printed_page'] for r in old}
    urls=json.loads((OUT/'page_urls.json').read_text(encoding='utf-8'))
    pending={r['printed_page']:r for r in json.loads((OUT/'batch_pending.json').read_text(encoding='utf-8'))}
    new=[]
    for page,(types,candidates) in SPECS.items():
        if page in seen: continue
        filename=f'p{page:03}.png' if page<100 else ('actual_p100.png' if page==100 else f'p{page-1:03}.png')
        path=OUT/'temp'/filename
        data=path.read_bytes()
        sha=hashlib.sha256(data).hexdigest()
        url=pending[page]['publisher_page_url'] if page<100 else urls[page-1]
        if page<100: assert sha==pending[page]['source_image_sha256']
        new.append(dict(grade=1,volume=2,printed_page=page,publisher_page_url=url,source_image_sha256=sha,image_bytes=len(data),evidence_level='ACTUAL_PUBLIC_PUBLISHER_IMAGE_VIEWED',exercise_types=types,covered_source_ids=[],new_gap_candidate_ids=candidates,source_comparison_status='PENDING_EXACT_FULL_FIELD_ADJUDICATION',reviewer='replacement_agent_resume_g1_page_audit',footer_page_verified=True,uncertainty='Actual image read; candidate is not an automatic gap. Physical ruler lengths and unseen outcomes are not inferred.'))
    with (OUT/'page_review.jsonl').open('a',encoding='utf-8',newline='\n') as f:
        for r in new:f.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n')
    # Glossary p106 was also visibly inspected; it is not mathematical content.
    gloss=OUT/'temp/p105.png'
    if gloss.exists():
        data=gloss.read_bytes(); (OUT/'boundary_106.json').write_text(json.dumps(dict(printed_page=106,role='GLOSSARY',evidence_level='ACTUAL_PUBLIC_PUBLISHER_IMAGE_VIEWED',publisher_page_url=urls[105],source_image_sha256=hashlib.sha256(data).hexdigest(),image_bytes=len(data)),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    allrows=old+new; pages=sorted({r['printed_page'] for r in allrows})
    summary=dict(grade=1,volume=2,actual_pages_reviewed=pages,actual_page_count=len(pages),pending_content_pages=sorted(set(range(4,106))-set(pages)),all_content_images_actually_viewed=set(pages)==set(range(4,106)),semantic_mapping_complete=False,network_revoked=False,temporary_image_bytes=0,new_cases_authored=0,scope='Printed content 4–105; no assertion that all physical front/back pages were inspected.',replacement_agent_resume=True)
    (OUT/'annotations_088_105.json').write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for page in SPECS:
        filename=f'p{page:03}.png' if page<100 else ('actual_p100.png' if page==100 else f'p{page-1:03}.png')
        path=OUT/'temp'/filename
        if path.exists():path.unlink()
    if gloss.exists():gloss.unlink()
    print(json.dumps(dict(actual_page_count=len(pages),new_pages_recorded=len(new),pending_content_pages=summary['pending_content_pages'],receipt_sha256=hashlib.sha256((OUT/'page_review.jsonl').read_bytes()).hexdigest())))

if __name__=='__main__':main()
