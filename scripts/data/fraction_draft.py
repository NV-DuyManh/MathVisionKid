"""Offline-only candidate routing, never verified labels or production decisions."""
from formula_probe import normalize_math


def select_fraction_draft(baseline, candidate):
    if len(baseline)!=2:
        raise ValueError('A fraction requires exactly two original tiers')
    missing=[not part.strip() or '?' in part for part in baseline]
    usable=(any(missing) and candidate is not None and len(candidate)==2
            and all(part.strip() and '?' not in part for part in candidate)
            and all(unknown or normalize_math(old)==normalize_math(new)
                    for old,new,unknown in zip(baseline,candidate,missing)))
    parts=[new if unknown else old for old,new,unknown in zip(baseline,candidate,missing)] if usable else list(baseline)
    return dict(parts=parts,source='formula_suggestion' if usable else 'crnn',
                needs_source_review=True,status='MODEL_DRAFT',training_eligible=False)
