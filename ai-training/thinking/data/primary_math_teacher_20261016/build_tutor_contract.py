"""Record a read-only, source-anchored contract. Does not call the tutor/model."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]


def source(path, anchors):
    data = (PROJECT / path).read_bytes()
    return dict(path=path, sha256=hashlib.sha256(data).hexdigest(),
                evidence_kind="actual_repository_source_read_only", anchors=anchors)


contract = {
    "contract_id": "mathvisionkid_actual_tutor_contract_20261016",
    "status": "SOURCE_VERIFIED_NOT_RUNTIME_EXECUTED",
    "source_precedence": "Actual checked-out code overrides claims in a comparison document.",
    "sources": [
        source("ai/runtime/app/tutoring/lesson.py", [
            {"line": 19, "symbol": "LessonRequest/TurnRequest", "supports": "confirmed source and owner/session/revision boundary"},
            {"line": 44, "symbol": "Step/Plan/DraftStep/PlanDraft", "supports": "exact generation fields and validation bounds"},
            {"line": 162, "symbol": "calculate_exact/expression_at", "supports": "AST arithmetic and previous-calculation references"},
            {"line": 230, "symbol": "PLAN_PROMPT", "supports": "teaching, refusal, source references and private worked help"},
            {"line": 305, "symbol": "REVIEW_PROMPT", "supports": "independent semantic checks and initial/worked teaching separation"},
            {"line": 421, "symbol": "formula_constants/validate_plan", "supports": "allowed source numbers, constants and prior answers"},
            {"line": 527, "symbol": "present", "supports": "public step fields and completion conclusion"},
            {"line": 617, "symbol": "guidance_at", "supports": "how private help is filtered before deep requests"},
            {"line": 645, "symbol": "generate_plan", "supports": "local schema/teaching validation followed by separate semantic review"},
            {"line": 766, "symbol": "answer_lesson", "supports": "hint_count, exact pupil answers, completed steps and revision"},
        ]),
        source("ai/runtime/app/tutoring/service.py", [
            {"line": 34, "symbol": "TutorModel", "supports": "extra=forbid and whitespace stripping"},
            {"line": 44, "symbol": "GuideRequest/GuideResponse", "supports": "hintLevel0..2 and stage-specific stateless hints"},
            {"line": 88, "symbol": "GUIDE_PROMPT", "supports": "all levels answer-free, no digits/equations, one hint/question"},
        ]),
        source("ai/runtime/app/api/tutor.py", [
            {"line": 20, "symbol": "lesson_endpoint/lesson_answer_endpoint/guide_endpoint", "supports": "internal API and failure mapping"},
        ]),
        source("backend/business-api/src/main/java/com/mathvisionkids/api/tutoring/MathTutorDtos.java", [
            {"line": 55, "symbol": "LessonRequest/LessonAnswer/LessonStep/CompletedStep/LessonResponse", "supports": "actual business API DTO boundary"},
        ]),
        source("backend/business-api/src/main/java/com/mathvisionkids/api/tutoring/MathTutorService.java", [
            {"line": 151, "symbol": "lessonResponse", "supports": "public output bounds, allowed statuses and conclusion only on COMPLETE"},
        ]),
    ],
    "not_actual_app_fields": {
        "initialGuidance": "No such PlanDraft/Step field exists; actual generated field is guidance.",
        "initialTeaching": "Review-only array resolved by server from guidance before deep help, not a planner output field.",
        "workedTeaching": "Review-only private paragraphs resolved by server, not a planner output field.",
        "deepSupport": "No standalone generation field; private worked guidance and the deeper hint implement support.",
    },
    "generation_contract": {
        "model": "app.tutoring.lesson.PlanDraft",
        "exact_top_level_fields": ["canSolve", "topic", "goal", "steps", "finalAnswerStep"],
        "canSolve": "strict boolean; false must carry steps=[] and finalAnswerStep=null; no fabricated answer.",
        "false_runtime_behavior": "False drafts are not published as lessons. generate_plan raises and can attempt one content repair; failure is unavailable at start_lesson.",
        "steps": "Solvable published Plan requires2..6 steps; Draft may contain0..6 to permit honest refusal.",
        "finalAnswerStep": "zero-based integer0..5, including choice indices, pointing to requested calculation; null for multiple requested results, not the numerical answer.",
        "exact_step_fields": ["title", "solutionSentence", "explanation", "guidance", "question", "choices", "correctChoice", "expression", "unit", "workExcerpt", "workLineIndexes", "hints", "fractionNotation"],
        "bounds": {"topic": 120, "goal": 220, "title": 100, "solutionSentence": 220,
                   "explanation": 500, "question": 220, "expression": 160, "unit": 20,
                   "choice_count_max": 4, "choice_chars_max": 100, "guidance_count_max": 6,
                   "guidance_paragraph_chars_max": 500, "hints_count_max": 3, "hint_chars_max": 500,
                   "workLineIndexes_count_max": 3, "draft_workExcerpt_length": 0},
        "calculation_step": "Nonempty expression; choices=[] and correctChoice=''; solutionSentence names quantity and ends là: without result. Question asks quantity amount.",
        "choice_step": "expression='' and solutionSentence='';2..4 text choices with correctChoice exactly matching a choice; each step needs choices XOR expression.",
        "teaching_order": "For one-operation problem, prepend useful comprehension choice to meet2step lesson; multi-operation problems begin with real calculation and avoid filler choices.",
        "guidance_prompt": "4paragraphs requested, each90..450characters: quantities, why/order, starting action, private worked currentstep. First3 must not reveal current/future computed values.",
        "guidance_runtime": "3..6paragraphs and >=240totalcharacters; initial resolved view>=2paragraphs and>=180characters; each paragraph<=500 after ref resolution. These syntactic checks do not establish semantic quality.",
        "hint_prompt": "2different hints: starting action and deeper worked help, <=450characters requested; no futurestep answers.",
        "source_work": "draft workExcerpt must be empty. workLineIndexes references0..2 original lines in increasing unique order; server copies contiguous source span between first/last. Never invent or correct pupil text.",
        "pedagogy": ["Explain quantities, why an operation answers the question and why the order matters.",
                     "Use equal parts/groups and simple concrete language; no algebraic transposition or elimination for primary pupils.",
                     "Do not infer an unobserved mental mistake from a wrong final equality alone.",
                     "Distinguish dimensionless share from count/length/mass and keep pupil unit errors out of teacher answers."],
    },
    "safe_arithmetic_contract": {
        "implementation": "calculate_exact uses bounded ast with fractions.Fraction and original decimal literal text, never eval.",
        "operators": ["+", "-", "*", "/", "parentheses", "unary_minus"],
        "symbol_translation": {"×": "*", "÷": "/", ":": "/", "−": "-"},
        "limits": {"ast_nodes_max": 50, "absolute_final_value_max": "1000000000000"},
        "unsupported": ["//", "% as remainder operator", "**", "variable names", "function calls", "units inside expressions"],
        "decimal_convention": "Planner formula decimal literals use dot. Pupil input and checked written equalities normalize comma to dot separately. calculate_exact itself does not normalize a comma decimal.",
        "division": "Rational division remains exact:52/6=26/3, not8. A remainder problem needs an explicit Euclidean quotient/remainder contract; do not mislabel rational division as integer quotient.",
        "source_operands": "Whole numerical literals from confirmed problemText givenNumbers; no arbitrary model-supplied constants or silently changed operands.",
        "formula_constants": {"always": ["1", "2"], "place_value_context": ["9", "10"], "percentage_context": ["100"], "time_context": ["60"]},
        "dependency_reference": "{sN} resolves exactly checked earlier calculationN. N is0-based among all steps including choices. First step cannot reference; no future/choice references.",
        "guidance_references": ["{sN}", "{sN_numerator}", "{sN_denominator}"],
        "derived_numbers": "Use prior calculation refs rather than embedding computed literals. validator attempts to turn matching derived numbers/reciprocals into previous-step refs; authoring should emit correct refs directly.",
        "quantity_faithfulness": "Using permitted digits does not prove correct roles/relationships; independent semantic review is still mandatory.",
    },
    "actual_runtime_presentation": {
        "request_confirmations": "problemConfirmed=true; workConfirmed=true if nonempty workText; no unread[?] tokens. Business API supplies authenticated owner.",
        "lesson_hint_modes": "hint_count0 shows starting hint; later hints may show CURRENTstep worked answer. present opens worked guidance when hint_count>=2. This is not the same policy as stateless guide hints.",
        "current_formula_visibility": "Generator formula is private to planning/review, but present intentionally resolves and displays the current-step expression without its answer. Future-step formula and answer keys are not public.",
        "public_step_fields": ["title", "explanation", "question", "choices", "expression", "unit", "workExcerpt", "solutionSentence", "guidance"],
        "not_public": ["correctChoice", "hints array", "fractionNotation", "workLineIndexes", "future steps and answers"],
        "completed_step_fields": ["title", "expression", "answer", "unit", "explanation", "solutionSentence", "calculationDetails", "guidance"],
        "status_values": ["READY", "HINT", "TRY_AGAIN", "CORRECT", "COMPLETE"],
        "step_transition": "Owner/session/revision checked; exact fractional pupil value must match calculator; successful answer advances revision and resets hint count.",
        "conclusion": "Only after completion and one finalAnswerStep: Đáp số plus exact checked answer and unit. Multiple requestedresults rely on completed steps; finalAnswerStep null.",
    },
    "independent_review_contract": {
        "model": "app.tutoring.lesson.PlanReview",
        "fields": ["sourceFaithful", "mathematicsCorrect", "answersQuestion", "teachingClear", "results", "issues"],
        "results_fields": ["stepIndex", "answer", "unit"],
        "checks": "Re-solve original problem independently; all4booleanchecks true and requested-result list nonempty; exact answer+unit agree with candidate calculated answers and final step semantics.",
        "limitations": "Separate model review plus deterministic arithmetic is a pipeline requirement, not a guarantee or a human/teacher certification.",
    },
    "stateless_guide_contract": {
        "model": "app.tutoring.service.GuideRequest/GuideResponse",
        "stages": ["UNDERSTAND", "PLAN", "NEXT_STEP", "CHECK_WORK"],
        "hintLevel": "strict integer0..2; alllevels answer-free.",
        "response_fields": ["stage", "hint", "question", "feedback", "guarded"],
        "generation_fields": ["stage", "hint", "question", "feedback"],
        "content": "ONE hint and ONE guiding question; Vietnamese; no digits, numbers spelled out, equations, full solutions, technical names or URLs. CHECK_WORK needs actual studentAttempt and may invite review without certifying correctness.",
        "seed_mapping": "Neutral hints levels1..3 may map to guide hintLevel0..2 only after no-number, one-question, stage/pedagogy review. Neutral seeds are not automatically accepted runtime requests.",
    },
    "neutral_teacher_schema": {
        "why_neutral": "Generate reusable, verifiable training material first, keeping full worked answer separate from answer-free hint modes. Do not claim source rows are immediately valid PlanDraft.",
        "exact_seed_keys": ["sample_id", "split", "case_group_id", "grade", "topic", "problem", "givens", "requested_quantity", "student_work", "initial_guidance", "hints", "worked_steps", "expected_answer", "canonical_case", "provenance", "quality_flags"],
        "givens_fields": ["id", "text", "value", "unit", "role"],
        "worked_step_fields": ["step_id", "title", "reason", "expression", "result", "unit", "explanation"],
        "hints_fields": ["level", "hint", "question"],
        "expected_answer_fields": ["quantity", "result", "unit"],
        "task_modes": {"worked_solution": "Full visible classroom explanation on explicit request; reason+exact steps+units+answer.",
                       "hint_1": "Conceptual immediate action, no computed answer.",
                       "hint_2": "More concrete operation/role help, no computed answer.",
                       "hint_3": "Specific starting technique, still no computed answer.",
                       "observed_work_review": "Address only supplied visible evidence; never invent pupil thoughts or corrected source.",
                       "clarify": "Ask for genuinely missing/ambiguous information without guessing."},
        "app_adapter_requirements": ["Map initial_guidance and private worked help into guidance explicitly; do not emit a nonexistent initialGuidancefield.",
                                     "Map exact results to server evidence, not to public initial explanation.",
                                     "Add useful choice only when necessary for one-operation lesson; validate2..6step limit.",
                                     "Set finalAnswerStep by requested result(s), counting any choice prefix in indices.",
                                     "Map work observations to true original workLineIndexes only when source rows exist.",
                                     "Handle unsupported Euclidean division/place-value constants in an explicit bounded extension or hold those rows back from app-specific export.",
                                     "Run actual source schema/local arithmetic checks and separate semantic review before integration."],
        "provenance_policy": "original_AI_teacher, human_verified=false, trainonly; curriculum node pending unless primary source mapping independently checked; no fake100%/gold claims.",
    },
    "changes_made_to_app": False,
    "external_model_calls": 0,
    "training_steps": 0,
    "skills_applied": [],
}

target = HERE / "tutor_contract.json"
target.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"file": target.name, "bytes": target.stat().st_size,
                  "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                  "source_files": len(contract["sources"])}))
