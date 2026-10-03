from app.schemas.core import ParsedExercise

class VerticalSubtractionValidator:
    def validate(self, parsed: ParsedExercise) -> dict:
        if parsed.status != "VALID_STRUCTURE":
            return {"is_valid": False, "evidence": []}
            
        try:
            op1 = int(parsed.operands[0])
            op2 = int(parsed.operands[1])
            res = int(parsed.result)
            
            if op1 - op2 == res:
                return {"is_valid": True, "evidence": []}
            else:
                width = max(len(parsed.operands[0]), len(parsed.operands[1]), len(parsed.result))
                str_op1 = parsed.operands[0].zfill(width)
                str_op2 = parsed.operands[1].zfill(width)
                str_res = parsed.result.zfill(width)
                
                borrow = 0
                for i in range(width - 1, -1, -1):
                    col_op1 = int(str_op1[i]) - borrow
                    col_op2 = int(str_op2[i])
                    col_res = int(str_res[i])
                    
                    next_borrow = 0
                    if col_op1 < col_op2:
                        col_op1 += 10
                        next_borrow = 1
                        
                    expected_digit = col_op1 - col_op2
                    
                    if col_res != expected_digit:
                        column = width - 1 - i
                        names = ["đơn vị", "chục", "trăm", "nghìn", "chục nghìn", "trăm nghìn", "triệu"]
                        place_value = names[column] if column < len(names) else f"10^{column}"
                        token = next((t for t in parsed.tokens if t.tokenClass == "digit"
                                      and t.row == 2 and t.column == column), None)
                        return {
                            "is_valid": False,
                            "evidence": [{
                                "evidenceId": "err_sub_1",
                                "type": "CARRY_BORROW_ERROR" if borrow > 0 else "COMPUTATION_ERROR",
                                "columnIndex": column,
                                "tokenId": token.tokenId if token else None,
                                "boundingBox": token.boundingBox if token else None,
                                "observedText": token.value if token else None,
                                "placeValue": f"Hàng {place_value}",
                                "ruleId": "SUB_COL_MISMATCH",
                                "confidence": 0.95,
                                "description": f"Phép trừ hàng {place_value} không khớp."
                            }]
                        }
                    borrow = next_borrow
                    
                return {"is_valid": False, "evidence": []}
        except ValueError:
            return {"is_valid": False, "evidence": []}
