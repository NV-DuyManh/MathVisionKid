"""Known incomplete notation needs a source correction, never a guessed answer."""
import re

from app.tutoring.service import _fold


class SourceNeedsReview(ValueError):
    def __init__(self, issue):
        self.issue = issue
        super().__init__('The source needs an explicit clarification')


def source_issue(source):
    text = _fold(source)
    if re.search(r'\(\s*\?\s*\)\s*[/⁄]\s*(?:\d+|\(\s*(?:\d+|\?)\s*\))'
                 r'|(?:\d+|\(\s*\d+\s*\))\s*[/⁄]\s*\(\s*\?\s*\)', text):
        return 'unread_fraction'
    if re.search(r'\d\(\s*\d+\s*(?:/|\)\s*/)', text):
        return 'mixed_number'
    if (re.search(r'\bm(?:²|\^2|2)(?!\w)', text)
            and re.search(r'thu hoach duoc\s+(?:\(\s*\d+\s*\)|\d+)\s*/\s*(?:\(\s*\d+\s*\)|\d+)\s+thoc\b', text)
            and re.search(r'bao nhieu\s+(?:ta|kg|ki[ -]lo)', text)):
        return 'missing_yield_unit'
    stem = re.split(r'(?<!\w)A[.)]', source, maxsplit=1)[0]
    if (re.search(r'lam tron den\s+\d', _fold(stem))
            and not re.search(r'hang\s+|so tu nhien|gan nhat', _fold(stem))):
        return 'rounding_place'
    return None


def require_clear_source(source):
    issue = source_issue(source)
    if issue:
        raise SourceNeedsReview(issue)
