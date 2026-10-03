from typing import List, Optional
from app.schemas.core import ImageRecognitionResult, ParsedExercise, Token

class StructuredParser:
    def parse(self, recognition_result: ImageRecognitionResult,
              allowed_operations: Optional[List[str]] = None, max_digits: int = 6,
              one_exercise_only: bool = True) -> ParsedExercise:
        tokens = recognition_result.tokens
        operators = [t for t in tokens if t.tokenClass == "operator"]
        digits = [t for t in tokens if t.tokenClass == "digit"]
        digit_rows = {t.row for t in digits if t.row is not None}

        # Keep every detection; a page with several exercises must never grade its first three rows.
        if len(operators) > 1 or any(r not in (0, 1, 2) for r in digit_rows):
            return ParsedExercise(operationType="UNKNOWN", operands=[], result="", tokens=tokens,
                                  status="INVALID_LAYOUT", reasonCode=("MULTIPLE_EXERCISES" if one_exercise_only
                                                                       else "MULTIPLE_EXERCISES_UNSUPPORTED"))
        if recognition_result.status == "NO_DETECTIONS":
            return ParsedExercise(operationType="UNKNOWN", operands=[], result="", tokens=[], status="NO_CONTENT_DETECTED")

        if recognition_result.status == "OUT_OF_SCOPE":
            return ParsedExercise(operationType="UNKNOWN", operands=[], result="", tokens=tokens, status="OUT_OF_SCOPE")
            
        if recognition_result.status == "UNCERTAIN_RECOGNITION":
            return ParsedExercise(operationType="UNKNOWN", operands=[], result="", tokens=recognition_result.tokens, status="UNCERTAIN_STRUCTURE")
            
        # Group by rows (0, 1, 2)
        rows = {0: [], 1: [], 2: []}
        operator = None
        for t in tokens:
            if t.row is not None and t.row in rows:
                rows[t.row].append(t)
            if t.tokenClass == "operator":
                operator = t.value
                
        # Sort each row by column (descending to read left-to-right correctly if column 0 is ones, column 1 is tens)
        # Assuming column 0 is units, 1 is tens, etc.
        for r in rows:
            rows[r].sort(key=lambda x: x.column if x.column is not None else -1, reverse=True)
            
        def build_number(row_tokens: List[Token]) -> str:
            digits = [t.value for t in row_tokens if t.tokenClass == "digit"]
            return "".join(digits)
            
        op1 = build_number(rows[0])
        op2 = build_number(rows[1])
        res = build_number(rows[2])
        
        op_type = "UNKNOWN"
        if operator == "+":
            op_type = "VERTICAL_ADDITION"
        elif operator == "-":
            op_type = "VERTICAL_SUBTRACTION"
            
        if not op1 or not op2 or not res or op_type == "UNKNOWN":
            return ParsedExercise(operationType=op_type, operands=[op1, op2], result=res, tokens=tokens, status="INVALID_LAYOUT")

        if (len(operators) != 1 or operators[0].row != 1
                or any(t.row is None or t.column is None or t.value not in "0123456789" or len(t.value) != 1
                       for t in digits)
                or any(sorted(t.column for t in rows[r] if t.tokenClass == "digit")
                       != list(range(sum(t.tokenClass == "digit" for t in rows[r]))) for r in rows)):
            return ParsedExercise(operationType=op_type, operands=[op1, op2], result=res, tokens=tokens,
                                  status="INVALID_LAYOUT", reasonCode="INVALID_LAYOUT")

        reason = None
        if allowed_operations is not None and op_type not in allowed_operations:
            reason = "OPERATION_NOT_ALLOWED"
        elif not 1 <= max_digits <= 6:
            reason = "UNSUPPORTED_DIGIT_LIMIT"
        elif max(len(op1), len(op2)) > max_digits or len(res) > max_digits + (operator == "+"):
            reason = "MAX_DIGITS_EXCEEDED"
        elif operator == "-" and int(op1) < int(op2):
            reason = "NEGATIVE_RESULT_UNSUPPORTED"
        if reason:
            return ParsedExercise(operationType=op_type, operands=[op1, op2], result=res, tokens=tokens,
                                  status="OUT_OF_SCOPE", reasonCode=reason)
            
        return ParsedExercise(
            operationType=op_type,
            operands=[op1, op2],
            result=res,
            tokens=tokens,
            status="VALID_STRUCTURE"
        )
