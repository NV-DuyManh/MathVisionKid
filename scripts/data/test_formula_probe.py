import pytest

from formula_probe import normalize_math, fraction_parts, pair_fraction_components


def test_normalization_only_changes_math_presentation_not_digit_values():
    assert normalize_math(r'\left( 300 \div 3 \right)') == '(300:3)'
    assert normalize_math('300 cm²') == normalize_math(r'300\mathrm{cm}^{2}')
    assert normalize_math('300') != normalize_math('30')
    assert normalize_math('1/3') != normalize_math('1/5')
    assert normalize_math('x') != normalize_math(r'\times')


@pytest.mark.parametrize('value,expected', [
    (r'\frac{13}{7}', ('13', '7')),
    (r'\dfrac{15 : 3}{21 : 3}', ('15:3', '21:3')),
    (r'\frac{5}{0}', ('5', '0')),
    (r'\frac{7}{13}', ('7', '13')),
    (r'\frac{13}{}', None),
    (r'\frac{13}', None),
    (r'\frac{13}{7}+1', None),
])
def test_complete_fraction_keeps_tiers_literal_and_rejects_incomplete_or_extra_math(value, expected):
    assert fraction_parts(value) == expected


def component(ident, role, box, source='a', split='TRAIN'):
    return dict(id=ident, math_role=role, box=box, split=split,
                source=dict(sha256=source))


def test_pairing_uses_geometry_not_label_and_never_crosses_source_or_split():
    rows = [component('n', 'numerator', [10,10,30,30]),
            component('d', 'denominator', [10,40,30,60]),
            component('other', 'denominator', [10,40,30,60],source='other'),
            component('dev', 'denominator', [10,40,30,60],split='DEV')]
    assert pair_fraction_components(rows) == [('n', 'd')]
    assert pair_fraction_components([rows[0], rows[2]]) == []
    assert pair_fraction_components([rows[0], rows[3]]) == []


def test_ambiguous_or_missing_fraction_tier_does_not_get_invented():
    n = component('n', 'numerator', [10,10,30,30])
    d = component('d', 'denominator', [10,40,30,60])
    other = component('d2', 'denominator', [12,40,32,60])
    assert pair_fraction_components([n]) == []
    assert pair_fraction_components([n,d,other]) == []
    assert pair_fraction_components([n,component('d', 'denominator', [80,40,100,60])]) == []
