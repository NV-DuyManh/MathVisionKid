"""Trọng tài chính: trích + so khớp đáp án SỐ. Hiểu định dạng số VN (46.080.000 / 3,75) lẫn Anh."""
import re


def _to_num(s):
    """Chuẩn hóa chuỗi số -> float, phân biệt dấu ngăn cách nghìn vs thập phân (VN và Anh)."""
    if s is None:
        return None
    s = re.sub(r"\s", "", str(s).strip())
    if not s:
        return None
    neg = s.startswith("-")
    s = s.lstrip("+-")
    dots, commas = s.count("."), s.count(",")
    if dots and commas:
        # dấu xuất hiện SAU cùng là dấu thập phân
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")   # VN: 1.234.567,89
        else:
            s = s.replace(",", "")                       # Anh: 1,234,567.89
    elif commas:
        parts = s.split(",")
        # 1 dấu phẩy + phần sau != 3 chữ số  -> thập phân VN (3,75); còn lại -> ngăn nghìn
        s = s.replace(",", ".") if (commas == 1 and len(parts[1]) != 3) else s.replace(",", "")
    elif dots:
        parts = s.split(".")
        # 1 dấu chấm + phần sau != 3 chữ số -> thập phân (3.75); còn lại -> ngăn nghìn VN (1.000 / 46.080.000)
        if not (dots == 1 and len(parts[1]) != 3):
            s = s.replace(".", "")
    try:
        v = float(s)
        return -v if neg else v
    except ValueError:
        return None


def extract_answer(text):
    """Trích đáp án số từ output solver. Ưu tiên 'ĐÁP ÁN CUỐI', rồi \\boxed{}, rồi số cuối."""
    if not text:
        return None
    m = re.search(r"ĐÁP\s*ÁN\s*CUỐI\s*[:：]\s*(.+)", text, re.IGNORECASE)
    seg = m.group(1) if m else text
    m2 = re.search(r"\\boxed\{([^}]*)\}", seg)
    if m2:
        seg = m2.group(1)
    nums = re.findall(r"-?\d[\d.,\s]*\d|-?\d", seg)  # cụm số (cho phép . , khoảng trắng ngăn cách)
    return nums[-1].strip() if nums else None


def _normalize(x):
    if x is None:
        return None
    n = _to_num(x)
    return n if n is not None else str(x).strip()


def answers_match(a, b, tol=1e-6):
    """So khớp 2 đáp án: ưu tiên số (sai số nhỏ), fallback so chuỗi."""
    na, nb = _normalize(a), _normalize(b)
    if na is None or nb is None:
        return False
    if isinstance(na, float) and isinstance(nb, float):
        return abs(na - nb) <= tol
    return str(na) == str(nb)
