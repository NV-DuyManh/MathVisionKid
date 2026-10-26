import json
from pathlib import Path
ROOT=Path(__file__).parent/'cloud_publication/sgk_page_audit_20261019'
N='primary_20261016_g1_foundations_0002_count14'
T='primary_20261018_old_g1_numbers_100_0096_bundled_sticks_tens_units_write_read'
W='primary_20261018_old_g1_numbers_100_0096_digit_cards_zero_and_tens_placeholder'
F='primary_20261018_old_g1_numbers_100_0096_forward_number_line_cross_tens_blank'
Q='primary_20261016_g1_foundations_0002_sort_four'
J='primary_20261018_old_g1_add_sub_no_carry_100_0098_join_two_disjoint_ticket_groups_by_place'
S='primary_20261016_g1_operations_0003_choose_subtract'
U='primary_20261018_finite099_g1_words_unknown_category'
E='sgk_g12_20261019_expression_target_classification_02'
B='sgk_g12_20261019_conditional_board_game_01'
H='sgk_g12_20261019_hundred_grid_patch_01'
C='primary_20261016_g1_measurement_0006_cm_read_write'
L='primary_20261016_g1_measurement_0006_cm_compare_same_unit'
P='primary_20261016_g1_solids_assembly_0005_diagonal_cut_restore'
M='primary_20261016_g1_geometry_0004_four_shape_matching'
D='primary_20261016_g1_operations_0003_left_add_subtract'
def write(rows,volume=2,grade=1):
 own=ROOT/f'g{grade}v{volume}_audit';d={}
 for p,t,ids,g in rows:
  d[str(p)]={'exercise_types':t.split(';'),'covered_source_ids':ids,'new_gap_candidate_ids':g,'source_comparison_status':'NEAREST_TRAIN_FIELDS_TO_BE_FINALIZED_AFTER_FULL_FIELD_READ','uncertainty':'Text analogue only: visual recognition, hidden objects, diagram geometry or physical outcomes are not validated. Candidate means pending semantic adjudication, not automatically new data.'}
 name=own/f'annotations_{rows[0][0]:03d}_{rows[-1][0]:03d}.json';name.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(name)
