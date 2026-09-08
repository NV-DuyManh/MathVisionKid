#!/usr/bin/env python3
"""
MathVision Kids — Unified Local Runtime Diagnostics Tool
Checks the health of all MathVision Kids local development components:
  - Infrastructure (Docker, PostgreSQL, MinIO, Redis)
  - Application Services (Spring Boot, FastAPI, Celery Worker, Teacher Web)
  - Client / Configuration status (Student Mobile, AI Mode, Model Artifact)

Exit Codes:
  0 = All required components PASS (READY_FOR_DEMO)
  1 = One or more required components FAIL / NOT_RUNNING
"""

import sys
import os
import socket
import subprocess
import urllib.request
import urllib.error
import json
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AI_SERVICE_DIR = REPO_ROOT / "services" / "ai-service"
AI_VENV_PYTHON = AI_SERVICE_DIR / ".venv" / "Scripts" / "python.exe"
if not AI_VENV_PYTHON.exists():
    AI_VENV_PYTHON = AI_SERVICE_DIR / ".venv" / "bin" / "python"

# Results store
RESULTS = {}
FAILURES = []
FASTAPI_INFO = {}


def record_result(name: str, status: str, detail: str = "", fix: str = ""):
    RESULTS[name] = status
    if status in ("FAIL", "BLOCKED"):
        FAILURES.append((name, status, detail, fix))


def check_port(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ConnectionRefusedError):
        return False


def check_docker():
    try:
        proc = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if proc.returncode == 0:
            record_result("Docker", "PASS")
        else:
            record_result(
                "Docker", "FAIL",
                detail="Docker daemon is not responding.",
                fix="Start Docker Desktop and ensure Docker daemon is running."
            )
    except Exception as e:
        record_result(
            "Docker", "FAIL",
            detail=f"Docker command failed: {e}",
            fix="Install Docker Desktop and ensure 'docker' CLI is in system PATH."
        )


def check_postgres():
    if not check_port("localhost", 5432):
        record_result(
            "PostgreSQL", "FAIL",
            detail="PostgreSQL port 5432 is not reachable.",
            fix="docker compose -f services/business-api/docker-compose.yml up -d postgres"
        )
        return

    # Check database readiness using pg_isready inside container if docker is running
    try:
        proc = subprocess.run(
            ["docker", "exec", "mathvision-postgres", "pg_isready", "-U", "mathvision", "-d", "mathvision"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=4
        )
        if proc.returncode == 0:
            record_result("PostgreSQL", "PASS")
        else:
            record_result(
                "PostgreSQL", "WARN",
                detail=f"Port 5432 open, but pg_isready returned non-zero: {proc.stderr.strip()}",
                fix="Check PostgreSQL container logs: docker logs mathvision-postgres"
            )
    except Exception:
        # Fallback to port check
        record_result("PostgreSQL", "PASS")


def check_minio():
    if not check_port("localhost", 9000):
        record_result(
            "MinIO", "FAIL",
            detail="MinIO API port 9000 is not reachable.",
            fix="docker compose -f services/business-api/docker-compose.yml up -d minio"
        )
        return

    try:
        req = urllib.request.Request("http://localhost:9000/minio/health/live", method="GET")
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            if resp.status == 200:
                record_result("MinIO", "PASS")
            else:
                record_result(
                    "MinIO", "FAIL",
                    detail=f"MinIO health check returned HTTP {resp.status}",
                    fix="Check MinIO container logs: docker logs mathvision-minio"
                )
    except Exception as e:
        record_result(
            "MinIO", "FAIL",
            detail=f"Cannot reach MinIO health endpoint: {e}",
            fix="docker compose -f services/business-api/docker-compose.yml up -d minio"
        )


def check_redis():
    try:
        s = socket.create_connection(("localhost", 6379), timeout=2.0)
        s.sendall(b"PING\r\n")
        response = s.recv(1024).decode("utf-8", errors="ignore")
        s.close()
        if "PONG" in response:
            record_result("Redis", "PASS")
        else:
            record_result(
                "Redis", "FAIL",
                detail=f"Redis replied unexpectedly: {response.strip()}",
                fix="docker compose -f services/business-api/docker-compose.yml restart redis"
            )
    except Exception as e:
        record_result(
            "Redis", "FAIL",
            detail=f"Redis connection failed on localhost:6379: {e}",
            fix="docker compose -f services/business-api/docker-compose.yml up -d redis"
        )


def check_spring():
    try:
        req = urllib.request.Request("http://localhost:8080/actuator/health", method="GET")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "UP":
                record_result("Spring Boot", "PASS")
            else:
                record_result(
                    "Spring Boot", "WARN",
                    detail=f"Spring health status is {data.get('status')}",
                    fix="Inspect Spring logs: check runtime/logs/spring.log"
                )
    except urllib.error.URLError as e:
        record_result(
            "Spring Boot", "FAIL",
            detail=f"Spring Boot not reachable at http://localhost:8080: {e}",
            fix="Start Spring Boot: scripts/start-all.bat or cd services/business-api && .\\gradlew.bat bootRun"
        )
    except Exception as e:
        record_result(
            "Spring Boot", "FAIL",
            detail=f"Spring Boot health check error: {e}",
            fix="Inspect Spring logs: check runtime/logs/spring.log"
        )


def check_fastapi():
    try:
        req_health = urllib.request.Request("http://localhost:8000/health", method="GET")
        with urllib.request.urlopen(req_health, timeout=2.0) as resp:
            if resp.status != 200:
                record_result(
                    "FastAPI", "FAIL",
                    detail=f"FastAPI /health returned HTTP {resp.status}",
                    fix="Inspect FastAPI logs: check runtime/logs/fastapi.log"
                )
                return

        req_ready = urllib.request.Request("http://localhost:8000/ready", method="GET")
        with urllib.request.urlopen(req_ready, timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            FASTAPI_INFO.update(data)
            if data.get("status") == "ready":
                record_result("FastAPI", "PASS")
            else:
                record_result(
                    "FastAPI", "WARN",
                    detail=f"FastAPI /ready status: {data.get('status')}",
                    fix="Inspect FastAPI logs: check runtime/logs/fastapi.log"
                )
    except urllib.error.URLError as e:
        record_result(
            "FastAPI", "FAIL",
            detail=f"FastAPI not reachable at http://localhost:8000: {e}",
            fix="Start FastAPI: scripts/start-all.bat or cd services/ai-service && .\\.venv\\Scripts\\uvicorn app.main:app --port 8000"
        )
    except Exception as e:
        record_result(
            "FastAPI", "FAIL",
            detail=f"FastAPI error: {e}",
            fix="Inspect FastAPI logs: check runtime/logs/fastapi.log"
        )


def check_celery():
    # Attempt to ping Celery worker using python in ai-service venv
    python_bin = str(AI_VENV_PYTHON) if AI_VENV_PYTHON.exists() else sys.executable
    cmd = [
        python_bin,
        "-c",
        "import sys, os; sys.path.insert(0, os.getcwd()); from app.jobs.celery_app import celery_app; res = celery_app.control.ping(timeout=2.5); sys.exit(0 if res and len(res) > 0 else 1)"
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(AI_SERVICE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=8
        )
        if proc.returncode == 0:
            record_result("Celery Worker", "PASS")
        else:
            record_result(
                "Celery Worker", "FAIL",
                detail="Celery worker did not respond to control ping.",
                fix="Start Celery worker: cd services/ai-service && .\\.venv\\Scripts\\celery.exe -A app.jobs.celery_app worker --loglevel=info --pool=solo"
            )
    except subprocess.TimeoutExpired:
        record_result(
            "Celery Worker", "FAIL",
            detail="Celery worker ping timed out.",
            fix="Ensure Redis is running and start worker: cd services/ai-service && .\\.venv\\Scripts\\celery.exe -A app.jobs.celery_app worker --loglevel=info --pool=solo"
        )
    except Exception as e:
        record_result(
            "Celery Worker", "FAIL",
            detail=f"Celery inspection failed: {e}",
            fix="Ensure Celery is installed in services/ai-service/.venv"
        )


def check_teacher_web():
    # Check port 5173 or probe
    port = 5173
    url = f"http://localhost:{port}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            if resp.status == 200:
                record_result("Teacher Web", "PASS")
            else:
                record_result(
                    "Teacher Web", "WARN",
                    detail=f"Teacher Web returned HTTP {resp.status}",
                    fix="Check teacher-web terminal or runtime/logs/teacher-web.log"
                )
    except urllib.error.URLError as e:
        record_result(
            "Teacher Web", "FAIL",
            detail=f"Teacher Web not reachable at {url}: {e}",
            fix="Start Teacher Web: cd teacher-web && npm run dev"
        )
    except Exception as e:
        record_result(
            "Teacher Web", "FAIL",
            detail=f"Teacher Web check error: {e}",
            fix="Check teacher-web dev server"
        )


def check_student_mobile():
    app_json = REPO_ROOT / "app.json"
    if not app_json.exists():
        record_result("Student Mobile", "NOT_CONFIGURED")
        return

    # Check if Metro bundler is running on port 8081
    if check_port("localhost", 8081, timeout=0.5):
        record_result("Student Mobile", "RUNNING")
    else:
        record_result("Student Mobile", "CONFIGURED")


def main():
    print("============================================")
    print(" MathVision Kids -- Local Runtime Diagnostic")
    print("============================================")
    print()

    # Run checks
    check_docker()
    check_postgres()
    check_minio()
    check_redis()
    check_spring()
    check_fastapi()
    check_celery()
    check_teacher_web()
    check_student_mobile()

    # Format output items
    items = [
        ("Docker", RESULTS.get("Docker", "NOT_RUNNING")),
        ("PostgreSQL", RESULTS.get("PostgreSQL", "NOT_RUNNING")),
        ("MinIO", RESULTS.get("MinIO", "NOT_RUNNING")),
        ("Redis", RESULTS.get("Redis", "NOT_RUNNING")),
        ("Spring Boot", RESULTS.get("Spring Boot", "NOT_RUNNING")),
        ("FastAPI", RESULTS.get("FastAPI", "NOT_RUNNING")),
        ("Celery Worker", RESULTS.get("Celery Worker", "NOT_RUNNING")),
        ("Teacher Web", RESULTS.get("Teacher Web", "NOT_RUNNING")),
        ("Student Mobile", RESULTS.get("Student Mobile", "NOT_CONFIGURED")),
    ]

    for name, status in items:
        dots = "." * max(1, 23 - len(name))
        print(f"{name} {dots} {status}")

    print()
    ai_mode = FASTAPI_INFO.get("mode") or os.environ.get("RUNTIME_MODE", "FIXTURE")
    model_path = REPO_ROOT / "services" / "ai-service" / "models" / "yolov8n_mathvision_det_v1.pt"
    manifest_path = REPO_ROOT / "services" / "ai-service" / "models" / "model_manifest.json"

    if model_path.exists() and manifest_path.exists():
        model_artifact = "LOADED"
        primary_model = "MathVision-Kids-Detection"
        model_version = "1.0.0"
    else:
        model_artifact = "NOT_PROVIDED"
        primary_model = "None"
        model_version = "N/A"

    print(f"AI Mode ............... {ai_mode}")
    print(f"Primary Model ......... {primary_model}")
    print(f"Model Version ......... {model_version}")
    print(f"Model Artifact ........ {model_artifact}")
    print()

    # Determine overall status
    required_services = [
        "Docker", "PostgreSQL", "MinIO", "Redis",
        "Spring Boot", "FastAPI", "Celery Worker", "Teacher Web"
    ]
    all_pass = all(RESULTS.get(s) == "PASS" for s in required_services)

    if all_pass:
        overall = "READY_FOR_DEMO"
        print(f"Overall ............... {overall}")
        print("============================================")
        return 0
    else:
        overall = "NOT_READY"
        print(f"Overall ............... {overall}")
        print("============================================")
        print()
        print("Actionable Diagnostics & Fixes:")
        for name, status, detail, fix in FAILURES:
            print(f"  [{status}] {name}:")
            if detail:
                print(f"    Issue: {detail}")
            if fix:
                print(f"    Fix:   {fix}")
            print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
