"""
MathVision Kids — Parser & Rule Engine (F1)
Deterministic parser for vertical addition/subtraction from YOLO detections.
"""
from __future__ import annotations
import json
import math
from dataclasses import dataclass, field
from typing import Literal, Optional
from collections import defaultdict

DetectionDict = dict[str, float | int | str]

DIGIT_CLASSES = {"0","1","2","3","4","5","6","7","8","9"}
OPERATOR_CLASSES = {"+","-"}
EQUALS_CLASS = "="
CARRY_CLASS = "c1"

@dataclass
class Detection:
    class_id: int
    class_name: str
    confidence: float
    x_center: float
    y_center: float
    width: float
    height: float
    in_pixels: bool = False

    @classmethod
    def from_dict(cls, d: DetectionDict, class_names: list[str]) -> "Detection":
        class_id = int(d.get("class_id", d.get("class", 0)))
        class_name = str(d.get("class_name", d.get("name", class_names[class_id] if class_id < len(class_names) else str(class_id))))
        return cls(
            class_id=class_id,
            class_name=class_name,
            confidence=float(d.get("confidence", d.get("conf", 1.0))),
            x_center=float(d.get("x_center", d.get("x", 0.0))),
            y_center=float(d.get("y_center", d.get("y", 0.0))),
            width=float(d.get("width", d.get("w", 0.0))),
            height=float(d.get("height", d.get("h", 0.0))),
            in_pixels=bool(d.get("in_pixels", False)),
        )

    def to_normalized(self, img_w: int, img_h: int) -> "Detection":
        if self.in_pixels:
            return Detection(
                class_id=self.class_id,
                class_name=self.class_name,
                confidence=self.confidence,
                x_center=self.x_center / img_w,
                y_center=self.y_center / img_h,
                width=self.width / img_w,
                height=self.height / img_h,
                in_pixels=False,
            )
        return self


@dataclass
class Row:
    y_center: float
    detections: list[Detection] = field(default_factory=list)
    row_type: Literal["top","bottom","result","operator","unknown"] = "unknown"


@dataclass
class Column:
    index_from_right: int
    x_center: float
    top_digit: Optional[int] = None
    bottom_digit: Optional[int] = None
    student_digit: Optional[int] = None
    expected_digit: Optional[int] = None
    incoming_carry_or_borrow: int = 0
    outgoing_carry_or_borrow: int = 0
    correct: bool = False


@dataclass
class ParserConfig:
    conf_threshold: float = 0.25
    row_tolerance_factor: float = 0.6
    column_tolerance_factor: float = 0.4
    nms_iou_threshold: float = 0.5
    min_detections_per_row: int = 1


@dataclass
class ParseResult:
    status: Literal["ok","wrong","needs_review"]
    operation: Literal["+","-",""]
    top_number: str
    bottom_number: str
    student_result: str
    correct_result: str
    confidence: float
    first_error_column: Optional[int]
    columns: list[dict]
    warnings: list[str]


class ParserEngine:
    def __init__(self, config: Optional[ParserConfig] = None):
        self.config = config or ParserConfig()

    def parse(self, detections: list[DetectionDict], class_names: list[str],
              img_w: int = 640, img_h: int = 640) -> ParseResult:
        # Normalize
        dets = [Detection.from_dict(d, class_names).to_normalized(img_w, img_h) for d in detections]
        
        # Filter
        dets = self._filter_detections(dets)
        if not dets:
            return self._empty_result("no_detections")
        
        # NMS per class
        dets = self._nms_per_class(dets)
        
        # Group rows
        rows = self._group_rows(dets)
        if len(rows) < 2:
            return self._empty_result("insufficient_rows")
        
        # Classify rows
        rows = self._classify_rows(rows)
        
        # Build columns
        columns = self._build_columns(rows)
        if not columns:
            return self._empty_result("no_columns")
        
        # Extract numbers
        top_num, bottom_num, student_res, op = self._extract_numbers(columns, rows)
        
        # Multiple operators detected
        if op == "" and top_num == "":
            return self._empty_result("multiple_operators")
        
        # Compute correct result
        try:
            if op == "+":
                correct = str(int(top_num) + int(bottom_num))
            elif op == "-":
                top_val = int(top_num)
                bottom_val = int(bottom_num)
                if top_val < bottom_val:
                    # Top < Bottom: subtraction would be negative
                    # For vertical subtraction, this is a layout/grade issue
                    return self._empty_result("top_less_than_bottom")
                correct = str(top_val - bottom_val)
            else:
                return self._empty_result("no_operator")
        except ValueError:
            return self._empty_result("invalid_numbers")
        
        # Verify columns
        first_error, cols_detail = self._verify_columns(columns, correct, op)
        
        # Confidence
        conf = self._compute_confidence(dets, rows, columns)
        
        # Determine status
        base_status = "ok" if first_error is None else ("wrong" if first_error >= 0 else "needs_review")
        
        # Low confidence detections -> needs_review
        low_conf = any(d.confidence < 0.5 for d in dets)
        if base_status == "ok" and low_conf:
            status = "needs_review"
        else:
            status = base_status
        
        return ParseResult(
            status=status,
            operation=op,
            top_number=top_num,
            bottom_number=bottom_num,
            student_result=student_res,
            correct_result=correct,
            confidence=round(conf, 3),
            first_error_column=first_error,
            columns=cols_detail,
            warnings=self._generate_warnings(dets, rows, columns, op)
        )

    def _filter_detections(self, dets: list[Detection]) -> list[Detection]:
        out = []
        for d in dets:
            if d.class_name not in DIGIT_CLASSES | OPERATOR_CLASSES | {EQUALS_CLASS, CARRY_CLASS}:
                continue
            if d.confidence < self.config.conf_threshold:
                continue
            if d.width <= 0 or d.height <= 0:
                continue
            out.append(d)
        return out

    def _nms_per_class(self, dets: list[Detection]) -> list[Detection]:
        by_class = defaultdict(list)
        for d in dets:
            by_class[d.class_name].append(d)
        
        out = []
        for cls, cls_dets in by_class.items():
            cls_dets.sort(key=lambda x: -x.confidence)
            kept = []
            for d in cls_dets:
                keep = True
                for k in kept:
                    if self._iou(d, k) > self.config.nms_iou_threshold:
                        keep = False
                        break
                if keep:
                    kept.append(d)
            out.extend(kept)
        return out

    def _iou(self, a: Detection, b: Detection) -> float:
        ax1, ay1 = a.x_center - a.width/2, a.y_center - a.height/2
        ax2, ay2 = a.x_center + a.width/2, a.y_center + a.height/2
        bx1, by1 = b.x_center - b.width/2, b.y_center - b.height/2
        bx2, by2 = b.x_center + b.width/2, b.y_center + b.height/2
        
        ix1, iy1 = max(ax1, bx1), max(ay1, by1)
        ix2, iy2 = min(ax2, bx2), min(ay2, by2)
        
        if ix2 <= ix1 or iy2 <= iy1:
            return 0.0
        
        inter = (ix2 - ix1) * (iy2 - iy1)
        union = a.width * a.height + b.width * b.height - inter
        return inter / union if union > 0 else 0.0

    def _group_rows(self, dets: list[Detection]) -> list[Row]:
        if not dets:
            return []
        
        median_h = sorted(d.height for d in dets)[len(dets)//2]
        tolerance = median_h * self.config.row_tolerance_factor
        
        dets_sorted = sorted(dets, key=lambda d: d.y_center)
        rows = []
        current_row = Row(y_center=dets_sorted[0].y_center, detections=[dets_sorted[0]])
        
        for d in dets_sorted[1:]:
            if abs(d.y_center - current_row.y_center) <= tolerance:
                current_row.detections.append(d)
                current_row.y_center = sum(x.y_center for x in current_row.detections) / len(current_row.detections)
            else:
                rows.append(current_row)
                current_row = Row(y_center=d.y_center, detections=[d])
        rows.append(current_row)
        
        return rows

    def _classify_rows(self, rows: list[Row]) -> list[Row]:
        # Sort by y_center (top to bottom)
        rows.sort(key=lambda r: r.y_center)
        
        # Find rows containing operators
        op_rows = []
        for i, r in enumerate(rows):
            op_count = sum(1 for d in r.detections if d.class_name in OPERATOR_CLASSES)
            if op_count > 0:
                r.row_type = "bottom"  # operator row IS the bottom row
                r.op_count = op_count
            else:
                r.op_count = 0
        
        # Check for multiple operator rows
        op_rows_idx = [i for i, r in enumerate(rows) if r.op_count > 0]
        if len(op_rows_idx) > 1:
            # Multiple operator rows - ambiguous
            for i in op_rows_idx:
                rows[i].row_type = "unknown"
            return rows
        
        op_idx = op_rows_idx[0] if op_rows_idx else None
        
        if op_idx is not None:
            # Row immediately above operator is top
            if op_idx > 0:
                rows[op_idx - 1].row_type = "top"
            # Rows below operator are result
            for i in range(op_idx + 1, len(rows)):
                rows[i].row_type = "result"
        else:
            # No operator found - try to infer from structure
            if len(rows) >= 3:
                rows[0].row_type = "top"
                rows[1].row_type = "bottom"
                rows[2].row_type = "result"
            elif len(rows) == 2:
                rows[0].row_type = "top"
                rows[1].row_type = "bottom"
        
        # Sort within each row by x_center
        for r in rows:
            r.detections.sort(key=lambda d: d.x_center)
        
        return rows

    def _build_columns(self, rows: list[Row]) -> list[Column]:
        # Collect digit info per row
        row_digits = defaultdict(list)
        for r in rows:
            if r.row_type in ("top","bottom","result"):
                for d in r.detections:
                    if d.class_name in DIGIT_CLASSES:
                        row_digits[r.row_type].append((d.x_center, int(d.class_name)))
        
        if not any(row_digits.values()):
            return []
        
        # Use result row for column structure (most reliable)
        result_digits = row_digits.get("result", [])
        if result_digits:
            result_x = sorted(set(round(x, 3) for x, _ in result_digits))
            columns_x = sorted(result_x, reverse=True)
        else:
            all_x = []
            for digits in row_digits.values():
                for x, _ in digits:
                    all_x.append(x)
            columns_x = sorted(set(round(x, 3) for x in all_x), reverse=True)
        
        if not columns_x:
            return []
        
        # Pre-compute digit assignments per row (1-to-1 matching right-to-left)
        row_assignments = {}
        for r in rows:
            if r.row_type not in ("top","bottom","result"):
                continue
            digits = [(d.x_center, int(d.class_name)) for d in r.detections if d.class_name in DIGIT_CLASSES]
            if not digits:
                continue
            # Sort digits by x descending (right to left)
            digits_sorted = sorted(digits, key=lambda x: x[0], reverse=True)
            row_assignments[r.row_type] = [d for _, d in digits_sorted]
        
        columns = []
        for idx, cx in enumerate(columns_x):
            col = Column(index_from_right=idx, x_center=cx)
            for r in rows:
                if r.row_type not in ("top","bottom","result"):
                    continue
                
                # Get pre-assigned digit for this column index
                assigned_digits = row_assignments.get(r.row_type, [])
                if idx < len(assigned_digits):
                    digit_val = assigned_digits[idx]
                    if r.row_type == "top":
                        col.top_digit = assigned_digits[idx]
                    elif r.row_type == "bottom":
                        col.bottom_digit = assigned_digits[idx]
                    elif r.row_type == "result":
                        col.student_digit = assigned_digits[idx]
                # If no digit assigned for this column index, leave as None
            columns.append(col)
        
        return columns

    def _extract_numbers(self, columns: list[Column], rows: list[Row]) -> tuple[str, str, str, str]:
        # Check for multiple operators
        all_ops = []
        for r in rows:
            for d in r.detections:
                if d.class_name in OPERATOR_CLASSES:
                    all_ops.append(d.class_name)
        
        if len(all_ops) > 1:
            return "", "", "", ""  # Signal multiple operators
        
        op = ""
        for r in rows:
            if r.row_type == "bottom":
                for d in r.detections:
                    if d.class_name in OPERATOR_CLASSES:
                        op = d.class_name
                        break
        
        top_digits = [str(c.top_digit) for c in columns if c.top_digit is not None]
        bottom_digits = [str(c.bottom_digit) for c in columns if c.bottom_digit is not None]
        result_digits = [str(c.student_digit) for c in columns if c.student_digit is not None]
        
        # Reverse because columns are right-to-left
        top_num = "".join(reversed(top_digits))
        bottom_num = "".join(reversed(bottom_digits))
        student_res = "".join(reversed(result_digits))
        
        return top_num, bottom_num, student_res, op

    def _verify_columns(self, columns: list[Column], correct_result: str, op: str) -> tuple[Optional[int], list[dict]]:
        correct_digits = [int(d) for d in reversed(correct_result)]
        
        first_error = None
        carry = 0
        
        for i, col in enumerate(columns):
            col.incoming_carry_or_borrow = carry
            
            top = col.top_digit if col.top_digit is not None else 0
            bottom = col.bottom_digit if col.bottom_digit is not None else 0
            student = col.student_digit if col.student_digit is not None else None
            
            if op == "+":
                total = top + bottom + carry
                expected = total % 10
                carry = total // 10
            else:  # subtraction
                diff = top - bottom - carry
                if diff < 0:
                    diff += 10
                    carry = 1
                else:
                    carry = 0
                expected = diff
            
            col.outgoing_carry_or_borrow = carry
            col.expected_digit = expected
            
            if student is not None:
                col.correct = (student == expected)
                if not col.correct and first_error is None:
                    first_error = i
            else:
                col.correct = False
                if first_error is None:
                    first_error = -1
        
        cols_detail = []
        for c in columns:
            cols_detail.append({
                "index_from_right": c.index_from_right,
                "top_digit": c.top_digit,
                "bottom_digit": c.bottom_digit,
                "student_digit": c.student_digit,
                "expected_digit": c.expected_digit,
                "incoming_carry_or_borrow": c.incoming_carry_or_borrow,
                "outgoing_carry_or_borrow": c.outgoing_carry_or_borrow,
                "correct": c.correct,
            })
        
        return first_error, cols_detail

    def _compute_confidence(self, dets: list[Detection], rows: list[Row], columns: list[Column]) -> float:
        if not dets:
            return 0.0
        det_conf = sum(d.confidence for d in dets) / len(dets)
        
        # Penalty for missing expected detections
        penalty = 0
        for r in rows:
            if r.row_type in ("top","bottom","result") and len(r.detections) == 0:
                penalty += 0.1
        
        # Boost confidence for complete simple problems
        if len(dets) >= 5 and all(r.row_type in ("top","bottom","result","bottom") for r in rows if r.detections):
            penalty -= 0.1
        
        # Penalty for misaligned columns
        for c in columns:
            if c.top_digit is None or c.bottom_digit is None or c.student_digit is None:
                penalty += 0.05
        
        return max(0.0, min(1.0, det_conf - penalty))

    def _generate_warnings(self, dets: list[Detection], rows: list[Row], columns: list[Column], op: str) -> list[str]:
        warnings = []
        if not op:
            warnings.append("no_operator_detected")
        if any(r.row_type == "unknown" for r in rows):
            warnings.append("unknown_row_type")
        if len(columns) > 6:
            warnings.append("many_columns_maybe_multiple_problems")
        low_conf = [d for d in dets if d.confidence < 0.5]
        if low_conf:
            warnings.append(f"low_confidence_detections:{len(low_conf)}")
        return warnings

    def _empty_result(self, reason: str) -> ParseResult:
        return ParseResult(
            status="needs_review",
            operation="",
            top_number="",
            bottom_number="",
            student_result="",
            correct_result="",
            confidence=0.0,
            first_error_column=None,
            columns=[],
            warnings=[reason]
        )


def parse_detections(detections: list[DetectionDict], class_names: list[str],
                     img_w: int = 640, img_h: int = 640,
                     config: Optional[ParserConfig] = None) -> dict:
    """Main entry point: accepts detection dicts, returns JSON-serializable dict."""
    engine = ParserEngine(config)
    result = engine.parse(detections, class_names, img_w, img_h)
    return {
        "status": result.status,
        "operation": result.operation,
        "top_number": result.top_number,
        "bottom_number": result.bottom_number,
        "student_result": result.student_result,
        "correct_result": result.correct_result,
        "confidence": result.confidence,
        "first_error_column": result.first_error_column,
        "columns": result.columns,
        "warnings": result.warnings,
    }


if __name__ == "__main__":
    # Quick self-test
    class_names = ["0","1","2","3","4","5","6","7","8","9","+","-","=","c1"]
    test_dets = [
        {"class_id": 3, "class_name": "3", "confidence": 0.9, "x_center": 0.6, "y_center": 0.2, "width": 0.08, "height": 0.12},
        {"class_id": 8, "class_name": "8", "confidence": 0.9, "x_center": 0.5, "y_center": 0.2, "width": 0.08, "height": 0.12},
        {"class_id": 10, "class_name": "+", "confidence": 0.9, "x_center": 0.35, "y_center": 0.35, "width": 0.08, "height": 0.12},
        {"class_id": 4, "class_name": "4", "confidence": 0.9, "x_center": 0.6, "y_center": 0.35, "width": 0.08, "height": 0.12},
        {"class_id": 7, "class_name": "7", "confidence": 0.9, "x_center": 0.5, "y_center": 0.35, "width": 0.08, "height": 0.12},
        {"class_id": 8, "class_name": "8", "confidence": 0.9, "x_center": 0.6, "y_center": 0.5, "width": 0.08, "height": 0.12},
        {"class_id": 5, "class_name": "5", "confidence": 0.9, "x_center": 0.5, "y_center": 0.5, "width": 0.08, "height": 0.12},
    ]
    result = parse_detections(test_dets, class_names)
    print(json.dumps(result, indent=2))