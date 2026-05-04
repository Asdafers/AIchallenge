#!/usr/bin/env python3
"""WP9 Deployment Smoke Test — builds the Docker image, runs the container,
hits /demo, captures the response into a trace artifact.

Usage:
    python3 scripts/wp9_deployment_smoke.py
    python3 scripts/wp9_deployment_smoke.py --output fixtures/wp9_deployment_trace.json
    python3 scripts/wp9_deployment_smoke.py --skip-build   # reuse existing image
    python3 scripts/wp9_deployment_smoke.py --port 9090    # custom host port

Requires Docker. Exits 0 if the /demo endpoint returns a valid JSON trace
with all_passed == true.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import http.client
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "fixtures" / "wp9_deployment_trace.json"
IMAGE_NAME = "methodic-demo:smoke"
CONTAINER_NAME = "methodic-demo-smoke"


def _docker_build() -> dict:
    start = time.monotonic()
    result = subprocess.run(
        ["docker", "build", "-t", IMAGE_NAME, "."],
        capture_output=True, text=True, timeout=300, cwd=str(REPO_ROOT),
    )
    elapsed = time.monotonic() - start
    return {
        "success": result.returncode == 0,
        "duration_s": round(elapsed, 1),
        "stdout_tail": result.stdout.strip().split("\n")[-5:] if result.stdout else [],
        "stderr_tail": result.stderr.strip().split("\n")[-5:] if result.stderr else [],
    }


def _docker_cleanup() -> None:
    subprocess.run(
        ["docker", "rm", "-f", CONTAINER_NAME],
        capture_output=True, timeout=30,
    )


def _docker_run(port: int) -> dict:
    _docker_cleanup()
    result = subprocess.run(
        [
            "docker", "run", "-d",
            "--name", CONTAINER_NAME,
            "-p", f"{port}:8080",
            "-e", "PORT=8080",
            IMAGE_NAME,
        ],
        capture_output=True, text=True, timeout=30, cwd=str(REPO_ROOT),
    )
    container_id = result.stdout.strip()[:12] if result.returncode == 0 else None
    return {
        "success": result.returncode == 0,
        "container_id": container_id,
        "error": result.stderr.strip() if result.returncode != 0 else None,
    }


def _http_get(port: int, path: str, timeout: int = 5) -> tuple[int, bytes]:
    conn = http.client.HTTPConnection("localhost", port, timeout=timeout)
    try:
        conn.request("GET", path)
        resp = conn.getresponse()
        body = resp.read()
        return resp.status, body
    finally:
        conn.close()


def _wait_for_health(port: int, max_attempts: int = 20) -> dict:
    for i in range(max_attempts):
        try:
            status, _ = _http_get(port, "/health", timeout=5)
            if status == 200:
                return {"healthy": True, "attempts": i + 1}
        except (ConnectionError, OSError, http.client.HTTPException):
            pass
        time.sleep(1)
    return {"healthy": False, "attempts": max_attempts}


def _call_demo(port: int) -> dict:
    start = time.monotonic()
    try:
        status, body = _http_get(port, "/demo", timeout=300)
        elapsed = time.monotonic() - start
        data = json.loads(body.decode("utf-8"))
        return {
            "success": True,
            "status_code": status,
            "duration_s": round(elapsed, 1),
            "demo_trace": data,
        }
    except Exception as e:
        elapsed = time.monotonic() - start
        return {
            "success": False,
            "duration_s": round(elapsed, 1),
            "error": str(e),
        }


def _get_container_logs() -> str | None:
    result = subprocess.run(
        ["docker", "logs", CONTAINER_NAME],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode == 0:
        combined = (result.stdout + result.stderr).strip()
        lines = combined.split("\n")
        return "\n".join(lines[-20:]) if lines else None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="WP9: Deployment Smoke Test")
    parser.add_argument(
        "--output", type=str, default=None,
        help=f"Output trace (default: {DEFAULT_OUTPUT.relative_to(REPO_ROOT)})",
    )
    parser.add_argument("--skip-build", action="store_true", help="Skip docker build")
    parser.add_argument("--port", type=int, default=8081, help="Host port (default: 8081)")
    args = parser.parse_args()
    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT

    print("WP9 deployment smoke test")
    print(f"  image: {IMAGE_NAME}")
    print(f"  port: {args.port}")

    build_result = None
    if not args.skip_build:
        print("  building image...")
        build_result = _docker_build()
        if not build_result["success"]:
            print(f"  ERROR: docker build failed")
            for line in build_result.get("stderr_tail", []):
                print(f"    {line}")
            return 1
        print(f"  build ok ({build_result['duration_s']}s)")
    else:
        print("  skipping build (--skip-build)")

    print("  starting container...")
    run_result = _docker_run(args.port)
    if not run_result["success"]:
        print(f"  ERROR: docker run failed: {run_result.get('error')}")
        return 1
    print(f"  container {run_result['container_id']} started")

    try:
        print("  waiting for health check...")
        health = _wait_for_health(args.port)
        if not health["healthy"]:
            logs = _get_container_logs()
            print(f"  ERROR: container not healthy after {health['attempts']} attempts")
            if logs:
                print(f"  container logs:\n{logs}")
            return 1
        print(f"  healthy after {health['attempts']} attempt(s)")

        print("  calling /demo (this takes a moment)...")
        demo_result = _call_demo(args.port)
        if not demo_result["success"]:
            print(f"  ERROR: /demo call failed: {demo_result.get('error')}")
            return 1

        demo_trace = demo_result["demo_trace"]
        pipeline = demo_trace.get("pipeline", {})
        print(f"  /demo returned in {demo_result['duration_s']}s")
        print(f"  steps: {pipeline.get('steps_succeeded')}/{pipeline.get('steps_total')} passed")

        container_logs = _get_container_logs()

        trace = {
            "study_id": "WL-2026-Q2-MM",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "engine_label": "deployment_smoke_test",
            "honest_label": (
                "Local Docker smoke test — proves the container builds, starts, "
                "serves /demo, and orchestrates all WP steps. This is NOT a live "
                "Cloud Run deployment. See operator_steps in the demo trace for "
                "actual GCP deployment instructions."
            ),
            "smoke_test": {
                "image": IMAGE_NAME,
                "host_port": args.port,
                "build": build_result,
                "container": run_result,
                "health_check": health,
                "demo_call": {
                    "success": demo_result["success"],
                    "status_code": demo_result.get("status_code"),
                    "duration_s": demo_result["duration_s"],
                },
                "container_logs_tail": container_logs,
            },
            "demo_trace": demo_trace,
            "verification": {
                "all_steps_passed": pipeline.get("all_passed", False),
                "mode": demo_trace.get("mode"),
                "steps_succeeded": pipeline.get("steps_succeeded"),
                "steps_total": pipeline.get("steps_total"),
            },
        }

        output_path.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")

        all_passed = pipeline.get("all_passed", False)
        print(f"  all_passed: {all_passed}")
        print(f"  mode: {demo_trace.get('mode')}")
        print(f"  trace written to: {output_path}")

        return 0 if all_passed else 1

    finally:
        print("  cleaning up container...")
        _docker_cleanup()
        print("  done")


if __name__ == "__main__":
    sys.exit(main())
