"""Arithmetic must preserve detections and abstain before an unsafe grade."""
import copy
import pytest
from app.jobs.tasks import process_submission
from app.parsing.parser import StructuredParser
from app.recognition.yolo_adapter import YoloDetectionAdapter
from app.recognition.quality import QualityGate
from app.schemas.core import ImageRecognitionResult, Token
from app.schemas.jobs import JobRequest


def recognition(numbers=("45", "27", "72"), operator="+", ambiguous=False):
    tokens = []
    for row, number in enumerate(numbers):
        for col, digit in enumerate(reversed(number)):
            tokens.append(Token(tokenId=f"r{row}c{col}", value=digit, tokenClass="digit",
                                row=row, column=col, boundingBox=[.6-col*.1, .1+row*.2, .08, .1],
                                confidence=.4 if ambiguous else .95, ambiguity=ambiguous))
    tokens.append(Token(tokenId="op", value=operator, tokenClass="operator", row=1,
                        column=99, boundingBox=[.3, .3, .08, .1], confidence=.95))
    return ImageRecognitionResult(tokens=tokens, status="UNCERTAIN_RECOGNITION" if ambiguous else "SUCCESS")


def test_adapter_preserves_rows_after_third_and_parser_refuses_multiple_exercises():
    boxes = [{"class_id": digit, "confidence": .95, "xyxy": [600, row*130, 650, row*130+60]}
             for row, digit in enumerate((1, 2, 3, 4, 5, 9))]
    boxes += [{"class_id": 10, "confidence": .95, "xyxy": [500, row*130, 550, row*130+60]}
              for row in (1, 4)]
    result = YoloDetectionAdapter().process_detections(boxes, 1000, 1000)
    assert sum(t.tokenClass == "digit" for t in result.tokens) == 6
    assert {t.row for t in result.tokens if t.tokenClass == "digit"} == set(range(6))
    parsed = StructuredParser().parse(result)
    assert parsed.status == "INVALID_LAYOUT"
    assert parsed.reasonCode == "MULTIPLE_EXERCISES"
    assert parsed.tokens == result.tokens
    assert StructuredParser().parse(result, one_exercise_only=False).reasonCode == "MULTIPLE_EXERCISES_UNSUPPORTED"


@pytest.mark.parametrize("numbers,operator,allowed,max_digits,reason", [
    (("1234", "1", "1235"), "+", ["VERTICAL_ADDITION"], 3, "MAX_DIGITS_EXCEEDED"),
    (("45", "27", "72"), "+", ["VERTICAL_SUBTRACTION"], 3, "OPERATION_NOT_ALLOWED"),
    (("2", "5", "3"), "-", ["VERTICAL_SUBTRACTION"], 3, "NEGATIVE_RESULT_UNSUPPORTED"),
    (("1", "2", "3"), "+", ["VERTICAL_ADDITION"], 7, "UNSUPPORTED_DIGIT_LIMIT"),
])
def test_requested_constraints_abstain(numbers, operator, allowed, max_digits, reason):
    result = recognition(numbers, operator)
    original = copy.deepcopy(result.tokens)
    parsed = StructuredParser().parse(result, allowed, max_digits)
    assert parsed.status == "OUT_OF_SCOPE"
    assert parsed.reasonCode == reason
    assert parsed.tokens == original == result.tokens


def test_max_digits_allows_extra_addition_carry_digit_and_rejects_missing_column():
    result = recognition(("999", "1", "1000"))
    assert StructuredParser().parse(result, max_digits=3).status == "VALID_STRUCTURE"
    result.tokens[0].column = 3
    assert StructuredParser().parse(result).status == "INVALID_LAYOUT"


@pytest.mark.parametrize("ambiguous,allowed,expected_status,expected_diagnosis", [
    (False, ["VERTICAL_ADDITION"], "FEEDBACK_READY", "INVALID"),
    (True, ["VERTICAL_ADDITION"], "NEEDS_CONFIRMATION", "UNCERTAIN"),
    (False, ["VERTICAL_SUBTRACTION"], "OUT_OF_SCOPE", "OUT_OF_SCOPE"),
])
def test_callback_has_original_identified_tokens_and_truthful_validation(mocker, ambiguous, allowed,
                                                                         expected_status, expected_diagnosis):
    result = recognition(("45", "27", "62"), ambiguous=ambiguous)
    original = result.model_dump()["tokens"]
    mocker.patch("app.jobs.tasks.FixtureRecognitionEngine.recognize", return_value=result)
    callback = mocker.patch("app.jobs.tasks.send_callback")
    process_submission("boundary-job", {"submissionId": "s", "imageReference": "fixture://valid",
                                         "allowedOperations": allowed, "maxDigits": 3})
    payload = callback.call_args.args[1].model_dump()
    assert payload["status"] == expected_status
    assert payload["recognizedTokens"] == original
    assert payload["validation"]["diagnosisState"] == expected_diagnosis
    assert payload["studentFeedback"]["revealAnswer"] is False
    if expected_diagnosis == "INVALID":
        assert payload["validation"]["isValid"] is False
        evidence = payload["validation"]["evidence"][0]
        assert evidence["columnIndex"] == 1  # tens: counted from the right
        assert evidence["tokenId"] == "r2c1"
        assert evidence["boundingBox"] == result.tokens[-2].boundingBox
    else:
        assert payload["validation"]["isValid"] is None
        assert payload["diagnostics"]["validatorInvoked"] is False


def test_private_object_name_is_not_fixture_quality_evidence():
    assert QualityGate().check_preflight("minio://mathvision/valid-not-blank-corrupt-dark.jpg") == (True, None, [])


@pytest.mark.parametrize("max_digits", [0, 7])
def test_job_rejects_digit_limits_not_supported_by_parser(max_digits):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        JobRequest(jobId="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", submissionId="s",
                   imageReference="minio://mathvision/a.jpg", allowedOperations=["VERTICAL_ADDITION"],
                   maxDigits=max_digits)
