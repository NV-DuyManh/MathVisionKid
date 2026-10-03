from app.schemas.core import ParsedExercise

class VerticalAdditionValidator:
    def validate(self, parsed: ParsedExercise) -> dict:
        if parsed.status != "VALID_STRUCTURE":
            return {"is_valid": False, "evidence": []}
            
        try:
            op1 = int(parsed.operands[0])
            op2 = int(parsed.operands[1])
            res = int(parsed.result)
            
            if op1 + op2 == res:
                return {"is_valid": True, "evidence": []}
            else:
                width = max(len(parsed.operands[0]), len(parsed.operands[1]), len(parsed.result)) + 1
                str_op1 = parsed.operands[0].zfill(width)
                str_op2 = parsed.operands[1].zfill(width)
                str_res = parsed.result.zfill(width)
                
                carry = 0
                for i in range(width - 1, -1, -1):
                    col_op1 = int(str_op1[i])
                    col_op2 = int(str_op2[i])
                    col_res = int(str_res[i])
                    
                    expected_sum = col_op1 + col_op2 + carry
                    expected_digit = expected_sum % 10
                    next_carry = expected_sum // 10
                    
                    if col_res != expected_digit:
                        column = width - 1 - i
                        names = ["đơn vị", "chục", "trăm", "nghìn", "chục nghìn", "trăm nghìn", "triệu"]
                        place_value = names[column] if column < len(names) else f"10^{column}"
                        token = next((t for t in parsed.tokens if t.tokenClass == "digit"
                                      and t.row == 2 and t.column == column), None)
                        return {
                            "is_valid": False,
                            "evidence": [{
                                "evidenceId": "err_add_1",
                                "type": "CARRY_BORROW_ERROR" if carry > 0 else "COMPUTATION_ERROR",
                                "columnIndex": column,
                                "tokenId": token.tokenId if token else None,
                                "boundingBox": token.boundingBox if token else None,
                                "observedText": token.value if token else None,
                                "placeValue": f"Hàng {place_value}",
                                "ruleId": "ADD_COL_MISMATCH",
                                "confidence": 0.95,
                                "description": f"Phép cộng hàng {place_value} không khớp."
                            }]
                        }
                    carry = next_carry
                    
                return {"is_valid": False, "evidence": []}
        except ValueError:
            return {"is_valid": False, "evidence": []}
