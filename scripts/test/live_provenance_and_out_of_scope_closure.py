import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

SPRING_BASE = "http://127.0.0.1:8080"
FASTAPI_BASE = "http://127.0.0.1:8000"

def query_postgres(sql):
    cmd = ["docker", "exec", "mathvision-postgres", "psql", "-U", "mathvision", "-d", "mathvision", "-t", "-A", "-c", sql]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        return f"ERROR: {res.stderr.strip()}"
    return res.stdout.strip()

def http_json(method, url, data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8') if data is not None else None,
        headers=headers,
        method=method
    )
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8')
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode('utf-8')
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, {"raw": content}

def post_multipart(url, fields, files, token=None):
    boundary = f'----WebKitFormBoundary{uuid.uuid4().hex[:16]}'
    body = bytearray()
    
    for k, v in fields.items():
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode('utf-8'))
        body.extend(str(v).encode('utf-8'))
        body.extend(b'\r\n')
        
    for k, (filename, data, content_type) in files.items():
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="{k}"; filename="{filename}"\r\n'.encode('utf-8'))
        body.extend(f'Content-Type: {content_type}\r\n\r\n'.encode('utf-8'))
        body.extend(data)
        body.extend(b'\r\n')
        
    body.extend(f'--{boundary}--\r\n'.encode('utf-8'))
    
    headers = {'Content-Type': f'multipart/form-data; boundary={boundary}'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
        
    req = urllib.request.Request(url, data=bytes(body), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8')
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode('utf-8')
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, {"raw": content}

def determine_result_route(submission):
    """
    Exact Python mirror of resolveResultRoute from src/utils/resultRouting.ts
    """
    status = submission.get("status")
    reason_code = submission.get("reasonCode")
    
    if status in ("NEEDS_RETAKE", "CROP_REQUIRED"):
        return "/results/quality-failure"
    if status == "OUT_OF_SCOPE" or reason_code == "OUT_OF_SCOPE":
        return "/results/out-of-scope"
    if status == "NEEDS_CONFIRMATION":
        return "/results/token-confirmation"
    if status == "REVIEW_REQUIRED":
        return "/results/review-required"
        
    decision = (submission.get("validation") or {}).get("decision")
    if decision == "VALID" or (status == "FEEDBACK_READY" and decision != "INVALID"):
        return "/results/correct"
        
    return "/results/error-hint"

def main():
    print("=" * 80)
    print("PROVENANCE CLOSURE & OUT-OF-SCOPE LIVE HTTP EVIDENCE")
    print("=" * 80)
    
    # 1. Health checks
    print("\n--- 1. Health Verification ---")
    st, sp_h = http_json("GET", f"{SPRING_BASE}/actuator/health")
    print(f"Spring Boot /actuator/health: status={st}, body={sp_h}")
    assert st == 200 and sp_h.get("status") == "UP"
    
    st, fa_r = http_json("GET", f"{FASTAPI_BASE}/ready")
    print(f"FastAPI /ready: status={st}, body={fa_r}")
    assert st == 200 and fa_r.get("status") == "ready" and fa_r.get("model_loaded") is True
    assert fa_r.get("mode") == "MODEL"
    print(f"FastAPI Mode: {fa_r.get('mode')}, Checkpoint SHA256: {fa_r.get('checkpoint_sha256')}")

    # 2. Student login
    print("\n--- 2. Student Authentication ---")
    st, auth_data = http_json("POST", f"{SPRING_BASE}/api/v1/auth/login", {
        "email": "minh.student@mathvision.local",
        "password": "MathVision123!"
    })
    assert st == 200, f"Login failed: {auth_data}"
    student_token = auth_data["accessToken"]
    print(f"Logged in student: minh.student@mathvision.local (Token acquired)")

    # 3. Live MODEL Trace (Arithmetic Submission)
    print("\n" + "=" * 80)
    print("SCENARIO 1: LIVE MODEL ARITHMETIC SUBMISSION (PROVENANCE VERIFICATION)")
    print("=" * 80)
    fixture_path = "services/ai-service/tests/fixtures/synthetic_addition.jpg"
    assert os.path.exists(fixture_path), f"Fixture missing: {fixture_path}"
    with open(fixture_path, "rb") as f:
        img_bytes = f.read()

    print(f"Submitting image: {fixture_path} ({len(img_bytes)} bytes)")
    t0 = time.time()
    st, sub_resp = post_multipart(
        f"{SPRING_BASE}/api/v1/student/submissions",
        {"source": "CAMERA"},
        {"image": ("exercise.jpg", img_bytes, "image/jpeg")},
        token=student_token
    )
    print(f"Submission accepted: HTTP {st}, response={sub_resp}")
    assert st == 202
    sub_id = sub_resp["submissionId"]

    # Poll
    final_sub = None
    for i in range(30):
        time.sleep(1.0)
        st, poll_resp = http_json("GET", f"{SPRING_BASE}/api/v1/student/submissions/{sub_id}", token=student_token)
        curr_status = poll_resp.get("status")
        print(f"  [POLL {i+1}] elapsed={time.time()-t0:.2f}s, status={curr_status}")
        if curr_status not in ("PROCESSING", "IMAGE_UPLOADED"):
            final_sub = poll_resp
            break

    assert final_sub is not None, "Scenario 1 timed out"
    elapsed_scen1 = time.time() - t0
    print(f"\nScenario 1 completed in {elapsed_scen1:.2f}s:")
    print(f"  submissionId: {sub_id}")
    print(f"  status: {final_sub.get('status')}")
    print(f"  reasonCode: {final_sub.get('reasonCode')}")
    print(f"  diagnostics: {json.dumps(final_sub.get('diagnostics'), indent=2)}")

    # Query Postgres
    pg_ar = query_postgres(f"SELECT submission_id, status, model_version, confidence, student_feedback, review_reasons FROM analysis_results WHERE submission_id = '{sub_id}';")
    pg_job = query_postgres(f"SELECT job_id, status, submitted_at, completed_at FROM ai_jobs WHERE submission_id = '{sub_id}';")
    print(f"\nPostgreSQL analysis_results row:\n{pg_ar}")
    print(f"PostgreSQL ai_jobs row:\n{pg_job}")

    # Inspect persisted model_version
    persisted_model_ver = query_postgres(f"SELECT model_version FROM analysis_results WHERE submission_id = '{sub_id}' LIMIT 1;").split('\n')[-1].strip()
    print(f"\n--> PERSISTED MODEL VERSION: '{persisted_model_ver}'")
    assert "MODEL:" in persisted_model_ver, f"Expected MODEL provenance, got: {persisted_model_ver}"
    assert "fixture-v1" not in persisted_model_ver, f"FATAL: still persisted fixture-v1: {persisted_model_ver}"

    # Route check
    route1 = determine_result_route(final_sub)
    print(f"Mobile route resolved: {route1}")
    assert route1 == "/results/correct"

    # 4. Live OUT_OF_SCOPE Trace
    print("\n" + "=" * 80)
    print("SCENARIO 2: LIVE OUT_OF_SCOPE HTTP SUBMISSION")
    print("=" * 80)
    oos_fixture_path = "services/ai-service/tests/fixtures/synthetic_subtraction_detected.jpg"
    assert os.path.exists(oos_fixture_path), f"Fixture missing: {oos_fixture_path}"
    with open(oos_fixture_path, "rb") as f:
        oos_img_bytes = f.read()

    print(f"Submitting image: {oos_fixture_path} ({len(oos_img_bytes)} bytes)")
    t0 = time.time()
    st, oos_sub_resp = post_multipart(
        f"{SPRING_BASE}/api/v1/student/submissions",
        {"source": "CAMERA"},
        {"image": ("exercise_oos.jpg", oos_img_bytes, "image/jpeg")},
        token=student_token
    )
    print(f"Submission accepted: HTTP {st}, response={oos_sub_resp}")
    assert st == 202
    oos_sub_id = oos_sub_resp["submissionId"]

    # Poll
    final_oos = None
    for i in range(30):
        time.sleep(1.0)
        st, poll_resp = http_json("GET", f"{SPRING_BASE}/api/v1/student/submissions/{oos_sub_id}", token=student_token)
        curr_status = poll_resp.get("status")
        print(f"  [POLL {i+1}] elapsed={time.time()-t0:.2f}s, status={curr_status}")
        if curr_status not in ("PROCESSING", "IMAGE_UPLOADED"):
            final_oos = poll_resp
            break

    assert final_oos is not None, "Scenario 2 timed out"
    elapsed_scen2 = time.time() - t0
    print(f"\nScenario 2 completed in {elapsed_scen2:.2f}s:")
    print(f"  submissionId: {oos_sub_id}")
    print(f"  status: {final_oos.get('status')}")
    print(f"  reasonCode: {final_oos.get('reasonCode')}")
    print(f"  diagnostics: {json.dumps(final_oos.get('diagnostics'), indent=2)}")

    # Query Postgres
    pg_oos_ar = query_postgres(f"SELECT submission_id, status, model_version, confidence, student_feedback, review_reasons FROM analysis_results WHERE submission_id = '{oos_sub_id}';")
    pg_oos_job = query_postgres(f"SELECT job_id, status, submitted_at, completed_at FROM ai_jobs WHERE submission_id = '{oos_sub_id}';")
    print(f"\nPostgreSQL analysis_results row (OOS):\n{pg_oos_ar}")
    print(f"PostgreSQL ai_jobs row (OOS):\n{pg_oos_job}")

    persisted_oos_model_ver = query_postgres(f"SELECT model_version FROM analysis_results WHERE submission_id = '{oos_sub_id}' LIMIT 1;").split('\n')[-1].strip()
    print(f"\n--> PERSISTED MODEL VERSION (OOS): '{persisted_oos_model_ver}'")

    # Mobile route check
    route2 = determine_result_route(final_oos)
    print(f"Mobile route resolved (OOS): {route2}")
    assert route2 == "/results/out-of-scope", f"Expected /results/out-of-scope, got: {route2}"

    print("\n" + "=" * 80)
    print("ALL LIVE HTTP PROVENANCE & OUT-OF-SCOPE ASSERTIONS PASSED PERFECTLY!")
    print("=" * 80)

if __name__ == "__main__":
    main()
