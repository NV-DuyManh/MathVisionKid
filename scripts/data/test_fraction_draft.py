from fraction_draft import select_fraction_draft


def test_fills_only_missing_tier_and_retains_draft_status():
    r=select_fraction_draft(['3',''],['3','5'])
    assert r['parts']==['3','5'] and r['source']=='formula_suggestion'
    assert r['needs_source_review'] and not r['training_eligible']


def test_known_tiers_are_never_overwritten_or_corrected_by_arithmetic():
    assert select_fraction_draft(['13','2'],['3','2'])['parts']==['13','2']
    assert select_fraction_draft(['15 : 3','21 : 3'],['5','7'])['source']=='crnn'


def test_contradicting_known_tier_or_incomplete_candidate_is_not_used():
    assert select_fraction_draft(['6',''],['9','7'])['parts']==['6','']
    assert select_fraction_draft(['3',''],None)['source']=='crnn'
    assert select_fraction_draft(['3',''],['3','[?]'])['source']=='crnn'


def test_unknown_tiers_and_zero_denominator_are_not_training_labels():
    r=select_fraction_draft(['?',''],['5','0'])
    assert r['parts']==['5','0']
    assert r['needs_source_review'] and not r['training_eligible']
