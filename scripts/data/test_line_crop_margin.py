import pytest
from line_crop_margin import pad_line_regions


def test_context_preserves_source_ink_and_cannot_bridge_rows_or_columns():
    boxes = [(0,10,80,30), (0,34,80,54), (85,10,145,30), (30,65,40,100)]
    grown = pad_line_regions(boxes,150,100)
    assert len(grown) == len(boxes)
    assert grown[0][3] <= grown[1][1] and grown[0][2] <= grown[2][0]
    assert grown[-1] == boxes[-1]  # Tall arithmetic is not a text row to expand.
    assert grown[0][1] < boxes[0][1] and grown[0][3] > boxes[0][3]
    for old,new in zip(boxes,grown):
        assert 0 <= new[0] <= old[0] < old[2] <= new[2] <= 150
        assert 0 <= new[1] <= old[1] < old[3] <= new[3] <= 100
    assert pad_line_regions([(0,0,100,20),(20,10,80,30)],100,40) == [(0,0,100,20),(20,10,80,30)]
    assert pad_line_regions([(0,0,100,20),(102,22,202,42)],210,50) == [(0,0,100,20),(102,22,202,42)]
    assert pad_line_regions([],100,40) == []


@pytest.mark.parametrize('boxes,width,height', [
    ([(0,0,101,20)],100,40), ([(0,0,30,20)],True,40),
    ([(10,10,10,20)],100,40), ([(0,0,30.0,20)],100,40),
    ([(0,0,30,20)]*501,100,40),
])
def test_invalid_geometry_is_rejected(boxes,width,height):
    with pytest.raises(ValueError): pad_line_regions(boxes,width,height)
