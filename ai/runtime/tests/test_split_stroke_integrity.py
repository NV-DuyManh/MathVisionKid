"""Row splitting must not slice faint stems or duplicate adjoining ink."""
import cv2
import numpy as np
import pytest

from app.recognition.text_detector import split_stacked_writing


def bands():
    image = np.full((140,160,3),248,np.uint8)
    for y in (20,65,110):
        for x in (20,65,110):
            cv2.rectangle(image,(x,y),(x+14,y+10),(140,40,20),-1)
    return image


def test_a_faint_connecting_stroke_cannot_be_cut_into_three_glyph_fragments():
    image = bands()
    cv2.line(image,(27,25),(27,120),(180,150,145),2)
    assert split_stacked_writing(image,(10,10,145,130)) == [(10,10,145,130)]


def test_independent_rows_stay_separate_on_a_faint_ruled_page():
    image = bands()
    cv2.line(image,(152,0),(152,139),(180,150,145),1)
    boxes = split_stacked_writing(image,(10,10,160,130))
    assert len(boxes)==3 and all(a[3]<=b[1] for a,b in zip(boxes,boxes[1:]))
    assert all(a<=20 and c>=125 and b<=y and d>=y+11
               for (a,b,c,d),y in zip(boxes,(20,65,110)))


def test_a_supported_faint_tail_expands_only_its_own_row():
    image = bands()
    cv2.line(image,(27,25),(27,47),(180,150,145),2)
    boxes = split_stacked_writing(image,(10,10,145,130))
    assert len(boxes)==3 and boxes[0][3]>=49
    assert boxes[0][3]<boxes[1][1] and boxes[1][3]<boxes[2][1]


@pytest.mark.parametrize('colour',[(140,40,20),(180,150,145)])
def test_stacked_fraction_is_not_split_even_when_its_bar_is_faint(colour):
    image = np.full((180,160,3),248,np.uint8)
    cv2.putText(image,'12',(30,60),cv2.FONT_HERSHEY_SIMPLEX,1,(140,40,20),2)
    cv2.line(image,(28,75),(76,75),colour,2)
    cv2.putText(image,'34',(30,115),cv2.FONT_HERSHEY_SIMPLEX,1,(140,40,20),2)
    assert split_stacked_writing(image,(20,20,100,140)) == [(20,20,100,140)]


def test_wide_distinct_baselines_keep_existing_row_geometry():
    image=np.full((150,650,3),248,np.uint8)
    for y in (40,100):
        cv2.putText(image,'120 + 35',(20,y),cv2.FONT_HERSHEY_SIMPLEX,1,(140,40,20),2)
    boxes=split_stacked_writing(image,(5,5,630,135))
    assert len(boxes)==2 and boxes[0][3]<boxes[1][1]
    assert boxes[0][3]<65 and boxes[1][1]>65
