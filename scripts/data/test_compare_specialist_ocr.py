from compare_specialist_ocr import select_draft


def test_route_is_role_based_and_agreement_never_verifies_training_label():
    hypotheses = dict(text='300 cm²', math='30 cm²', legacy='300 cm²')
    assert select_draft('prose', hypotheses)['text'] == '300 cm²'
    result = select_draft('expression', hypotheses)
    assert result['text'] == '30 cm²'
    assert result['review_reasons'] == ['model_disagreement']
    agreed = select_draft('expression', dict(text='wrong', math='wrong'))
    assert agreed['status'] == 'MODEL_DRAFT' and not agreed['training_eligible']


def test_fraction_tiers_preserve_literal_reading_without_solving():
    for literal in ('21 : 3', '0', '-7', '[?]'):
        result = select_draft('denominator', dict(text=literal, math=literal))
        assert result['text'] == literal
        assert 'fraction_tier_requires_linked_layout_review' in result['review_reasons']
        assert not result['training_eligible']
        if literal == '[?]':
            assert 'unresolved_glyph' in result['review_reasons']


def test_unknown_role_abstains_and_missing_reading_requires_review():
    result = select_draft(None, dict(text='hello', math='123'))
    assert result['selected_model'] is None and result['text'] == ''
    assert 'unknown_region_role' in result['review_reasons']
    assert 'empty_reading' in select_draft('prose', {})['review_reasons']
