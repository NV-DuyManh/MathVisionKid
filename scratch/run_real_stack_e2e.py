"""
True Real-Stack E2E Test Runner for Phase 4.0.3
Executes all 3 real cross-process E2E flows:
  1. Student True E2E (FEEDBACK_READY, 1 Socratic hint, revealAnswer=False)
  2. Teacher True E2E (Confident Invalid -> PROPOSED_GRADE, isOfficial=False, evidence)
  3. Teacher Uncertain E2E (Ambiguous -> REVIEW_REQUIRED)
All flows execute: Spring Boot -> HttpAiAnalysisGateway -> FastAPI -> Redis -> Celery -> Callback -> Spring Boot DB
"""

import io
import json
import time
import httpx
import subprocess

SPRING_BASE = "http://localhost:8080"
FASTAPI_BASE = "http://localhost:8000"

def get_token(email, password):
    resp = httpx.post(f"{SPRING_BASE}/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    return resp.json()["token"]

def psql_query(sql):
    cmd = ["docker", "exec", "mathvision-postgres", "psql", "-U", "mathvision", "-d", "mathvision", "-t", "-A", "-F", "|", "-c", sql]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return res.stdout.strip()

def run_tests():
    print("=" * 60)
    print("STARTING PHASE 4.0.3 TRUE REAL-STACK E2E VERIFICATION")
    print("=" * 60)

    # 1. Login
    student_token = get_token("minh.student@mathvision.local", "MathVision123!")
    teacher_token = get_token("lan.teacher@mathvision.local", "MathVision123!")
    print("[AUTH] Tokens acquired for Student and Teacher.")

    # ============================================================
    # SCENARIO 1: STUDENT TRUE E2E
    # ============================================================
    print("\n" + "=" * 50)
    print("SCENARIO 1: STUDENT TRUE E2E (Invalid arithmetic -> FEEDBACK_READY)")
    print("=" * 50)

    fake_img = b"STUDENT_TEST_IMAGE_BYTES"
    files = {"image": ("addition-carry-error.jpg", io.BytesIO(fake_img), "image/jpeg")}
    headers = {"Authorization": f"Bearer {student_token}"}
    
    sub_resp = httpx.post(f"{SPRING_BASE}/api/v1/student/submissions", files=files, data={"source": "CAMERA"}, headers=headers)
    print("Student submission response:", sub_resp.status_code, sub_resp.text)
    assert sub_resp.status_code == 202, f"Expected 202, got {sub_resp.status_code}"
    student_sub_id = sub_resp.json()["submissionId"]
    print(f"Created student submissionId: {student_sub_id}")

    # Wait for Celery worker and callback to Spring
    time.sleep(3)

    # Query DB for AiJob, Submission, and AnalysisResult
    job_info = psql_query(f"SELECT job_id, status, submission_id FROM ai_jobs WHERE submission_id = '{student_sub_id}';")
    print(f"Student AiJob record: {job_info}")
    assert job_info, "AiJob must exist in DB"
    job_id, job_status, _ = job_info.split("|")
    assert job_status == "COMPLETED", f"Expected AiJob COMPLETED, got {job_status}"

    sub_info = psql_query(f"SELECT status FROM submissions WHERE submission_id = '{student_sub_id}';")
    print(f"Student Submission status: {sub_info}")
    assert sub_info == "FEEDBACK_READY", f"Expected FEEDBACK_READY, got {sub_info}"

    ar_info = psql_query(f"SELECT status, student_feedback FROM analysis_results WHERE submission_id = '{student_sub_id}';")
    print(f"Student AnalysisResult: {ar_info}")
    ar_status, fb_json = ar_info.split("|", 1)
    assert ar_status == "FEEDBACK_READY"
    fb = json.loads(fb_json)
    assert fb["revealAnswer"] is False, "revealAnswer must be False"
    assert fb["hint"] != "", "hint must not be empty"
    print("-> Student Feedback Title:", fb.get("title"))
    print("-> Student Hint:", fb.get("hint"))
    print("-> revealAnswer:", fb.get("revealAnswer"))
    print("SCENARIO 1 RESULT: PASS")

    # ============================================================
    # SCENARIO 2 & 3: TEACHER TRUE E2E (Batch with Confident Invalid + Uncertain)
    # ============================================================
    print("\n" + "=" * 50)
    print("SCENARIOS 2 & 3: TEACHER TRUE E2E (Batch flow with 10 images)")
    print("=" * 50)

    # Teacher creates a batch
    t_headers = {"Authorization": f"Bearer {teacher_token}"}
    batch_resp = httpx.post(
        f"{SPRING_BASE}/api/v1/teacher/batches",
        json={"assignmentId": "22222222-2222-2222-2222-222222222222"},
        headers=t_headers
    )
    print("Batch create response:", batch_resp.status_code, batch_resp.text)
    assert batch_resp.status_code == 201, f"Batch create failed: {batch_resp.text}"
    batch_id = batch_resp.json()["batchId"]
    print(f"Created teacher batchId: {batch_id}")

    # Prepare 10 images to satisfy batch privacy gate (10 <= count <= 30)
    student_id = psql_query("SELECT student_id FROM students LIMIT 1;")
    batch_files = []
    manifest = []

    # File 0: addition-carry-error.jpg (Scenario 2: Confident Invalid -> PROPOSED_GRADE)
    batch_files.append(("images", ("addition-carry-error.jpg", io.BytesIO(b"IMG_0"), "image/jpeg")))
    manifest.append({"fileIndex": 0, "studentId": student_id})

    # File 1: ambiguous.jpg (Scenario 3: Uncertain Recognition -> REVIEW_REQUIRED)
    batch_files.append(("images", ("ambiguous.jpg", io.BytesIO(b"IMG_1"), "image/jpeg")))
    manifest.append({"fileIndex": 1, "studentId": student_id})

    # Files 2-9: valid addition images
    for i in range(2, 10):
        batch_files.append(("images", (f"valid-addition-{i}.jpg", io.BytesIO(f"IMG_{i}".encode()), "image/jpeg")))
        manifest.append({"fileIndex": i, "studentId": student_id})

    upload_data = {"manifest": json.dumps(manifest)}
    up_resp = httpx.post(
        f"{SPRING_BASE}/api/v1/teacher/batches/{batch_id}/submissions",
        files=batch_files,
        data=upload_data,
        headers=t_headers,
        timeout=30.0
    )
    print("Batch upload response:", up_resp.status_code)
    assert up_resp.status_code == 202, f"Upload failed: {up_resp.text}"

    # Wait for Celery worker to process all 10 submissions and send callbacks
    print("Waiting 6 seconds for Celery processing and callbacks...")
    time.sleep(6)

    # ── Verify Scenario 2: Confident Invalid -> PROPOSED_GRADE ──
    print("\n--- Verifying Scenario 2 (Confident Invalid) ---")
    sub_inv_id = psql_query(f"""
        SELECT s.submission_id 
        FROM submissions s 
        JOIN submission_images si ON s.submission_id = si.submission_id 
        WHERE s.batch_id = '{batch_id}' AND si.file_path LIKE '%addition-carry-error%' 
        LIMIT 1;
    """)
    print(f"Confident invalid submissionId: {sub_inv_id}")
    assert sub_inv_id, "Submission for addition-carry-error must exist"

    t_job_info = psql_query(f"SELECT job_id, status FROM ai_jobs WHERE submission_id = '{sub_inv_id}';")
    print(f"Teacher AiJob: {t_job_info}")
    t_job_id, t_job_status = t_job_info.split("|")
    assert t_job_status == "COMPLETED", f"Expected AiJob COMPLETED, got {t_job_status}"

    t_sub_status = psql_query(f"SELECT status FROM submissions WHERE submission_id = '{sub_inv_id}';")
    print(f"Teacher Submission status: {t_sub_status}")
    assert t_sub_status == "PROPOSED_GRADE", f"Expected PROPOSED_GRADE for confident invalid, got {t_sub_status}"

    t_ar_info = psql_query(f"SELECT status, grade_proposal, evidence FROM analysis_results WHERE submission_id = '{sub_inv_id}';")
    print(f"Teacher AnalysisResult: {t_ar_info}")
    t_ar_status, gp_json, ev_json = t_ar_info.split("|", 2)
    assert t_ar_status == "PROPOSED_GRADE"
    gp = json.loads(gp_json)
    assert gp["isOfficial"] is False, "gradeProposal.isOfficial must be False"
    assert gp["suggestedScore"] == 0, f"Expected suggestedScore 0 for invalid, got {gp['suggestedScore']}"
    assert gp["maxScore"] == 10
    assert gp["reason"] != ""
    ev = json.loads(ev_json)
    assert "items" in ev and len(ev["items"]) >= 1, "Evidence items must be present"
    print("-> Grade Proposal reason:", gp.get("reason"))
    print("-> Grade Proposal suggestedScore:", gp.get("suggestedScore"))
    print("-> Grade Proposal isOfficial:", gp.get("isOfficial"))
    print("-> Evidence items count:", len(ev["items"]))

    # Check TeacherDecision table: must be ABSENT
    dec_count = psql_query(f"SELECT COUNT(*) FROM teacher_decisions WHERE submission_id = '{sub_inv_id}';")
    assert dec_count == "0", f"TeacherDecision must not be automatically created, count was {dec_count}"
    print("-> TeacherDecision count: 0 (absent as required)")
    print("SCENARIO 2 RESULT: PASS")

    # ── Verify Scenario 3: Uncertain Recognition -> REVIEW_REQUIRED ──
    print("\n--- Verifying Scenario 3 (Uncertain Ambiguous Digit) ---")
    sub_unc_id = psql_query(f"""
        SELECT s.submission_id 
        FROM submissions s 
        JOIN submission_images si ON s.submission_id = si.submission_id 
        WHERE s.batch_id = '{batch_id}' AND si.file_path LIKE '%ambiguous%' 
        LIMIT 1;
    """)
    print(f"Uncertain submissionId: {sub_unc_id}")
    assert sub_unc_id, "Submission for ambiguous image must exist"

    u_job_info = psql_query(f"SELECT job_id, status FROM ai_jobs WHERE submission_id = '{sub_unc_id}';")
    print(f"Uncertain AiJob: {u_job_info}")
    u_job_id, u_job_status = u_job_info.split("|")
    assert u_job_status == "COMPLETED", f"Expected AiJob COMPLETED, got {u_job_status}"

    u_sub_status = psql_query(f"SELECT status FROM submissions WHERE submission_id = '{sub_unc_id}';")
    print(f"Uncertain Submission status: {u_sub_status}")
    assert u_sub_status == "REVIEW_REQUIRED", f"Expected REVIEW_REQUIRED for ambiguous digit, got {u_sub_status}"
    print("SCENARIO 3 RESULT: PASS (invalid != uncertain confirmed)")

    print("\n" + "=" * 60)
    print("ALL TRUE REAL-STACK E2E SCENARIOS PASSED WITH HTTP 2XX CALLBACKS!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
