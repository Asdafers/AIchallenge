#!/usr/bin/env python3
"""WP9 Cloud Run Demo Server — HTTP service that orchestrates the full
Methodic vertical slice and returns a structured demo trace.

Listens on $PORT (default 8080). Single endpoint: GET /demo runs all
work packages (WP3–WP9a) as subprocesses and collects per-step results.

Mode detection:
  - K_SERVICE env set        → cloud_run_live (running on Cloud Run)
  - Running inside container → local_container (docker run)
  - Neither                  → local_direct (python3 scripts/wp9_demo_server.py)

Usage:
    python3 scripts/wp9_demo_server.py              # start server
    PORT=9090 python3 scripts/wp9_demo_server.py    # custom port

Exits 0 on clean shutdown.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _detect_mode() -> dict:
    if os.environ.get("K_SERVICE"):
        return {
            "mode": "cloud_run_live",
            "reason": "K_SERVICE environment variable set by Cloud Run",
        }
    if Path("/.dockerenv").exists():
        return {
            "mode": "local_container",
            "reason": "Running inside Docker container (/.dockerenv present)",
        }
    return {
        "mode": "local_direct",
        "reason": "Running directly on host (no container detected)",
    }


DEMO_STEPS = [
    {
        "id": "wp3",
        "label": "External Request & Organizer Flow",
        "cmd": ["python3", "scripts/wp3_organizer_flow.py", "--output"],
        "output_name": "wp3_event_log.json",
    },
    {
        "id": "wp4",
        "label": "Methodology Pushback & Question Design",
        "cmd": ["python3", "scripts/wp4_methodology_review.py", "--mode", "fallback", "--output"],
        "output_name": "wp4_methodology_package.json",
    },
    {
        "id": "wp5",
        "label": "Participant Conversations & Coverage Loop",
        "cmd": ["python3", "scripts/wp5_conversation_engine.py", "--output-responses"],
        "output_name": "wp5_participant_responses.json",
        "extra_output_args": ["--output-coverage"],
        "extra_output_name": "wp5_coverage_summary.json",
    },
    {
        "id": "wp6",
        "label": "Real MCP Boundary (lookup_deal_context)",
        "cmd": ["python3", "scripts/wp6_mcp_boundary.py", "--output"],
        "output_name": "wp6_mcp_trace.json",
    },
    {
        "id": "wp7",
        "label": "Data Quality Scoring",
        "cmd": ["python3", "scripts/wp7_data_quality.py", "--output-report"],
        "output_name": "wp7_quality_report.json",
        "extra_output_args": ["--output-csv"],
        "extra_output_name": "wp7_quality_export.csv",
        "extra_output_args_2": ["--output-bigquery"],
        "extra_output_name_2": "wp7_bigquery_schema.json",
    },
    {
        "id": "wp8",
        "label": "Autonomous Re-Plan Trigger",
        "cmd": ["python3", "scripts/wp8_replan_trigger.py", "--output"],
        "output_name": "wp8_replan_trace.json",
    },
    {
        "id": "wp9a",
        "label": "BigQuery Export Setup (dry-run)",
        "cmd": ["python3", "scripts/wp9a_bigquery_export.py", "--dry-run", "--output"],
        "output_name": "wp9a_bigquery_export_trace.json",
    },
]


def _run_step(step: dict, tmp_dir: str) -> dict:
    """Run a single demo step, capturing output and timing."""
    start = datetime.now(timezone.utc)
    step_id = step["id"]

    try:
        primary_out = os.path.join(tmp_dir, step["output_name"])
        cmd = list(step["cmd"]) + [primary_out]

        if step_id == "wp5":
            coverage_out = os.path.join(tmp_dir, step["extra_output_name"])
            cmd += ["--output-coverage", coverage_out]
        elif step_id == "wp7":
            csv_out = os.path.join(tmp_dir, step["extra_output_name"])
            bq_out = os.path.join(tmp_dir, step["extra_output_name_2"])
            cmd += ["--output-csv", csv_out, "--output-bigquery", bq_out]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120, cwd=str(REPO_ROOT),
        )

        elapsed_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        stdout_lines = result.stdout.strip().split("\n") if result.stdout.strip() else []

        output_data = None
        if os.path.exists(primary_out):
            raw = Path(primary_out).read_text(encoding="utf-8")
            if primary_out.endswith(".json"):
                output_data = json.loads(raw)

        return {
            "step_id": step_id,
            "label": step["label"],
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "duration_ms": round(elapsed_ms, 1),
            "stdout_summary": stdout_lines[:5],
            "stderr_summary": (result.stderr.strip().split("\n")[:3] if result.stderr.strip() else None),
            "output_file": step["output_name"],
            "output_keys": list(output_data.keys()) if isinstance(output_data, dict) else None,
        }

    except subprocess.TimeoutExpired:
        elapsed_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        return {
            "step_id": step_id,
            "label": step["label"],
            "success": False,
            "exit_code": -1,
            "duration_ms": round(elapsed_ms, 1),
            "error": "timeout after 120s",
        }
    except Exception as e:
        elapsed_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        return {
            "step_id": step_id,
            "label": step["label"],
            "success": False,
            "exit_code": -1,
            "duration_ms": round(elapsed_ms, 1),
            "error": str(e),
        }


def _run_demo() -> dict:
    """Execute the full demo pipeline and return structured trace."""
    mode_info = _detect_mode()
    demo_start = datetime.now(timezone.utc)

    with tempfile.TemporaryDirectory() as tmp_dir:
        step_results = []
        for step in DEMO_STEPS:
            step_results.append(_run_step(step, tmp_dir))

    total_ms = (datetime.now(timezone.utc) - demo_start).total_seconds() * 1000
    succeeded = sum(1 for s in step_results if s["success"])
    failed = sum(1 for s in step_results if not s["success"])

    return {
        "study_id": "WL-2026-Q2-MM",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine_label": "cloud_run_demo_server",
        "honest_label": (
            f"Demo trace from {mode_info['mode']} mode. "
            f"WP4 forced to fallback mode (no GEMINI_API_KEY in container). "
            f"WP9a forced to dry-run (no BigQuery credentials). "
            f"This proves the vertical slice orchestration, not live cloud deployment."
        ),
        "mode": mode_info["mode"],
        "mode_reason": mode_info["reason"],
        "pipeline": {
            "steps_total": len(step_results),
            "steps_succeeded": succeeded,
            "steps_failed": failed,
            "total_duration_ms": round(total_ms, 1),
            "all_passed": failed == 0,
        },
        "steps": step_results,
        "operator_steps": {
            "description": "Steps to deploy this server to Cloud Run",
            "prerequisites": [
                "GCP project with Cloud Run API and Artifact Registry enabled",
                "gcloud CLI authenticated (gcloud auth login)",
                "Docker installed locally for building the image",
            ],
            "build_and_push": [
                "export PROJECT_ID=my-project-id",
                "export REGION=us-central1",
                "gcloud artifacts repositories create methodic --repository-format=docker --location=$REGION",
                "docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/methodic/demo-server:latest .",
                "docker push $REGION-docker.pkg.dev/$PROJECT_ID/methodic/demo-server:latest",
            ],
            "deploy": [
                (
                    "gcloud run deploy methodic-demo "
                    "--image $REGION-docker.pkg.dev/$PROJECT_ID/methodic/demo-server:latest "
                    "--region $REGION "
                    "--allow-unauthenticated "
                    "--set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID,BIGQUERY_DATASET=methodic"
                ),
            ],
            "iam_for_bigquery": {
                "description": "Grant the Cloud Run service account BigQuery access at dataset scope",
                "commands": [
                    (
                        "bq show --format=prettyjson $PROJECT_ID:methodic | "
                        "jq '.access += [{\"role\": \"WRITER\", \"userByEmail\": \"$SA_EMAIL\"}]' | "
                        "bq update --source /dev/stdin $PROJECT_ID:methodic"
                    ),
                    (
                        "gcloud projects add-iam-policy-binding $PROJECT_ID "
                        "--member=serviceAccount:$SA_EMAIL "
                        "--role=roles/bigquery.jobUser"
                    ),
                ],
                "note": "dataEditor scoped to dataset (not project) per least-privilege principle",
            },
            "verify": "curl https://methodic-demo-HASH-uc.a.run.app/demo | jq .",
        },
    }


class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/demo":
            trace = _run_demo()
            body = json.dumps(trace, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/health":
            body = b'{"status":"ok"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404, "Not found. Use /demo or /health")

    def log_message(self, format: str, *args: object) -> None:
        print(format % args, file=sys.stderr)


def main() -> int:
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), DemoHandler)
    print(f"WP9 demo server listening on 0.0.0.0:{port}", file=sys.stderr)
    print(f"  mode: {_detect_mode()['mode']}", file=sys.stderr)
    print(f"  endpoints: /demo, /health", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
