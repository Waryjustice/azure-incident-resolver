"""
Comprehensive End-to-End System Test for Azure Incident Resolver
================================================================
Tests all major components in order:
  1. Environment Setup
  2. Azure Services (Service Bus queues)
  3. Agent Imports
  4. Dashboard
  5. Demo Scenarios
  6. pytest Suite
  7. GitHub Connection
  8. Service Bus Connection

Outputs TEST_RESULTS.json and a human-readable console summary.
"""

import importlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Bootstrap: ensure project root is on sys.path and .env is loaded ──────────
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass  # Will be flagged in section 1 if dotenv is missing


# ── Helpers ───────────────────────────────────────────────────────────────────

class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed: bool | None = None
        self.details: list[str] = []
        self.errors: list[str] = []
        self.duration_ms: float = 0.0

    def ok(self, msg: str = ""):
        self.passed = True
        if msg:
            self.details.append(msg)

    def fail(self, msg: str = ""):
        self.passed = False
        if msg:
            self.errors.append(msg)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "details": self.details,
            "errors": self.errors,
            "duration_ms": round(self.duration_ms, 2),
        }


def run_section(label: str, fn) -> list[TestResult]:
    """Run a test section function and return its results."""
    print(f"\n{'═' * 60}")
    print(f"  {label}")
    print(f"{'═' * 60}")
    results = fn()
    for r in results:
        icon = "✅" if r.passed else "❌"
        print(f"  {icon}  {r.name}")
        for d in r.details:
            print(f"       ↳ {d}")
        for e in r.errors:
            print(f"       ✗ {e}")
    return results


# ── Section 1: Environment Setup ──────────────────────────────────────────────

REQUIRED_ENV_VARS = [
    "AZURE_SERVICEBUS_CONNECTION_STRING",
    "GITHUB_TOKEN",
    "AZURE_SUBSCRIPTION_ID",
    "AZURE_TENANT_ID",
    "AZURE_RESOURCE_GROUP",
    "AZURE_MONITOR_WORKSPACE_ID",
    "GITHUB_REPO_OWNER",
    "GITHUB_REPO_NAME",
]

OPTIONAL_ENV_VARS = [
    "AZURE_SQL_SERVER",
    "AZURE_SQL_DATABASE",
    "MONITORED_WEBAPP_ID",
    "AZURE_APP_INSIGHTS_KEY",
    "GITHUB_MODEL_NAME",
    "FLASK_SECRET_KEY",
    "LOG_LEVEL",
]


def test_environment() -> list[TestResult]:
    results: list[TestResult] = []

    # dotenv importable
    r = TestResult("python-dotenv installed")
    t0 = time.monotonic()
    try:
        import dotenv  # noqa: F401
        r.ok("python-dotenv is available")
    except ImportError as exc:
        r.fail(str(exc))
    r.duration_ms = (time.monotonic() - t0) * 1000
    results.append(r)

    # .env file present
    r = TestResult(".env file present")
    t0 = time.monotonic()
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        r.ok(str(env_path))
    else:
        r.fail(f".env not found at {env_path}")
    r.duration_ms = (time.monotonic() - t0) * 1000
    results.append(r)

    # Required vars
    missing = []
    present = []
    for var in REQUIRED_ENV_VARS:
        val = os.getenv(var, "")
        if val and not val.startswith("your-") and not val.startswith("ghp_your"):
            present.append(var)
        else:
            missing.append(var)

    r = TestResult("Required environment variables")
    t0 = time.monotonic()
    if not missing:
        r.ok(f"All {len(REQUIRED_ENV_VARS)} required variables are set")
    else:
        r.fail(f"Missing or placeholder values: {', '.join(missing)}")
        if present:
            r.details.append(f"Present: {', '.join(present)}")
    r.duration_ms = (time.monotonic() - t0) * 1000
    results.append(r)

    # Optional vars (informational — always pass)
    r = TestResult("Optional environment variables")
    t0 = time.monotonic()
    opt_set = [v for v in OPTIONAL_ENV_VARS if os.getenv(v, "")]
    opt_missing = [v for v in OPTIONAL_ENV_VARS if not os.getenv(v, "")]
    r.ok(f"{len(opt_set)}/{len(OPTIONAL_ENV_VARS)} optional vars set")
    if opt_missing:
        r.details.append(f"Not set (non-blocking): {', '.join(opt_missing)}")
    r.duration_ms = (time.monotonic() - t0) * 1000
    results.append(r)

    return results


# ── Section 2: Azure Services – Service Bus Queues ────────────────────────────

EXPECTED_QUEUES = [
    "detection-to-diagnosis",
    "diagnosis-to-resolution",
    "resolution-to-communication",
]


def test_azure_services() -> list[TestResult]:
    results: list[TestResult] = []
    conn_str = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING", "")
    is_placeholder = (not conn_str
                      or "your-namespace" in conn_str
                      or "your-shared-access-key" in conn_str)

    # SDK import check
    r = TestResult("azure-servicebus management SDK importable")
    t0 = time.monotonic()
    try:
        from azure.servicebus.management import ServiceBusAdministrationClient  # noqa: F401
        r.ok("ServiceBusAdministrationClient available")
    except ImportError as exc:
        r.fail(f"ImportError: {exc}")
    r.duration_ms = (time.monotonic() - t0) * 1000
    results.append(r)

    for queue in EXPECTED_QUEUES:
        r = TestResult(f"Service Bus queue: {queue}")
        t0 = time.monotonic()

        if is_placeholder:
            r.fail("AZURE_SERVICEBUS_CONNECTION_STRING not configured — skipping queue check")
            r.duration_ms = (time.monotonic() - t0) * 1000
            results.append(r)
            continue

        try:
            from azure.servicebus.management import ServiceBusAdministrationClient
            with ServiceBusAdministrationClient.from_connection_string(conn_str) as admin:
                props = admin.get_queue(queue)
                r.ok(f"Queue exists (name: {props.name})")
        except Exception as exc:
            err = str(exc)
            if "does not exist" in err.lower() or "404" in err or "not found" in err.lower():
                r.fail(f"Queue '{queue}' not found in Service Bus namespace")
            else:
                r.fail(f"{type(exc).__name__}: {err}")

        r.duration_ms = (time.monotonic() - t0) * 1000
        results.append(r)

    return results


# ── Section 3: Agent Imports ───────────────────────────────────────────────────

AGENTS = [
    ("DetectionAgent",    "src.agents.detection.agent",    "DetectionAgent"),
    ("DiagnosisAgent",    "src.agents.diagnosis.agent",    "DiagnosisAgent"),
    ("ResolutionAgent",   "src.agents.resolution.agent",   "ResolutionAgent"),
    ("CommunicationAgent","src.agents.communication.agent","CommunicationAgent"),
]


def test_agent_imports() -> list[TestResult]:
    results: list[TestResult] = []

    for label, module_path, class_name in AGENTS:
        r = TestResult(f"Import {label}")
        t0 = time.monotonic()
        try:
            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name)
            r.ok(f"{cls.__module__}.{cls.__name__} imported successfully")
        except ImportError as exc:
            r.fail(f"ImportError: {exc}")
        except AttributeError as exc:
            r.fail(f"Class not found: {exc}")
        except Exception as exc:
            r.fail(f"{type(exc).__name__}: {exc}")
        r.duration_ms = (time.monotonic() - t0) * 1000
        results.append(r)

    return results


# ── Section 4: Dashboard ───────────────────────────────────────────────────────

def test_dashboard() -> list[TestResult]:
    results: list[TestResult] = []

    dashboard_path = PROJECT_ROOT / "dashboard" / "app.py"

    # File exists
    r = TestResult("dashboard/app.py exists")
    t0 = time.monotonic()
    if dashboard_path.exists():
        r.ok(str(dashboard_path))
    else:
        r.fail(f"Not found: {dashboard_path}")
    r.duration_ms = (time.monotonic() - t0) * 1000
    results.append(r)

    # Import dashboard module
    r = TestResult("dashboard/app.py importable")
    t0 = time.monotonic()
    try:
        spec = importlib.util.spec_from_file_location("dashboard_app", dashboard_path)
        mod = importlib.util.module_from_spec(spec)
        # Redirect stdout to suppress startup prints
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            spec.loader.exec_module(mod)
        finally:
            sys.stdout = old_stdout
        r.ok("Module loaded without errors")
    except Exception as exc:
        r.fail(f"{type(exc).__name__}: {exc}")
    r.duration_ms = (time.monotonic() - t0) * 1000
    results.append(r)

    # Flask app object present
    r = TestResult("Flask 'app' object present in dashboard")
    t0 = time.monotonic()
    try:
        spec = importlib.util.spec_from_file_location("dashboard_app2", dashboard_path)
        mod = importlib.util.module_from_spec(spec)
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            spec.loader.exec_module(mod)
        finally:
            sys.stdout = old_stdout
        flask_app = getattr(mod, "app", None)
        if flask_app is not None:
            r.ok(f"app = {type(flask_app).__name__}")
        else:
            r.fail("No 'app' attribute found in dashboard/app.py")
    except Exception as exc:
        r.fail(f"{type(exc).__name__}: {exc}")
    r.duration_ms = (time.monotonic() - t0) * 1000
    results.append(r)

    return results


# ── Section 5: Demo Scenarios ──────────────────────────────────────────────────

def test_demo_scenarios() -> list[TestResult]:
    results: list[TestResult] = []
    examples_dir = PROJECT_ROOT / "examples"

    # Directory exists
    r = TestResult("examples/ directory exists")
    t0 = time.monotonic()
    if examples_dir.is_dir():
        r.ok(str(examples_dir))
    else:
        r.fail(f"Directory not found: {examples_dir}")
    r.duration_ms = (time.monotonic() - t0) * 1000
    results.append(r)

    demo_files = sorted(examples_dir.glob("demo-*.py"))

    # Count check
    r = TestResult(f"Demo files present (expected 11, found {len(demo_files)})")
    t0 = time.monotonic()
    if len(demo_files) == 11:
        r.ok(", ".join(f.name for f in demo_files))
    elif len(demo_files) > 0:
        r.fail(f"Expected 11 demo files, found {len(demo_files)}: {', '.join(f.name for f in demo_files)}")
    else:
        r.fail("No demo-*.py files found in examples/")
    r.duration_ms = (time.monotonic() - t0) * 1000
    results.append(r)

    # Parse each file (compile without executing)
    for demo_file in demo_files:
        r = TestResult(f"Parse {demo_file.name}")
        t0 = time.monotonic()
        try:
            source = demo_file.read_text(encoding="utf-8")
            compile(source, str(demo_file), "exec")
            r.ok("Syntax OK")
        except SyntaxError as exc:
            r.fail(f"SyntaxError at line {exc.lineno}: {exc.msg}")
        except Exception as exc:
            r.fail(f"{type(exc).__name__}: {exc}")
        r.duration_ms = (time.monotonic() - t0) * 1000
        results.append(r)

    return results


# ── Section 6: pytest Suite ────────────────────────────────────────────────────

def test_pytest_suite() -> list[TestResult]:
    results: list[TestResult] = []
    test_dir = PROJECT_ROOT / "src" / "agents" / "resolution"

    test_files = list(test_dir.glob("test_*.py"))

    r_files = TestResult("pytest test files found")
    t0 = time.monotonic()
    if test_files:
        r_files.ok(f"Found: {', '.join(f.name for f in test_files)}")
    else:
        r_files.fail(f"No test_*.py files in {test_dir}")
    r_files.duration_ms = (time.monotonic() - t0) * 1000
    results.append(r_files)

    if not test_files:
        return results

    r = TestResult("pytest suite passes")
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest"] + [str(f) for f in test_files] +
            ["-v", "--tb=short", "--no-header"],
            capture_output=True, text=True,
            cwd=str(test_dir),
            timeout=120,
        )
        output_lines = (proc.stdout + proc.stderr).splitlines()
        # Surface summary line
        summary = next(
            (ln for ln in reversed(output_lines) if "passed" in ln or "failed" in ln or "error" in ln),
            proc.stdout[-300:] if proc.stdout else "no output"
        )
        if proc.returncode == 0:
            r.ok(summary)
        else:
            r.fail(summary)
            # Include up to 20 lines of failure detail
            failure_lines = [ln for ln in output_lines if "FAILED" in ln or "ERROR" in ln or "AssertionError" in ln]
            for fl in failure_lines[:20]:
                r.errors.append(fl)
    except subprocess.TimeoutExpired:
        r.fail("pytest timed out after 120s")
    except Exception as exc:
        r.fail(f"{type(exc).__name__}: {exc}")
    r.duration_ms = (time.monotonic() - t0) * 1000
    results.append(r)

    return results


# ── Section 7: GitHub Connection ──────────────────────────────────────────────

def test_github_connection() -> list[TestResult]:
    results: list[TestResult] = []
    token = os.getenv("GITHUB_TOKEN", "")

    r = TestResult("GitHub token present")
    t0 = time.monotonic()
    if token and not token.startswith("ghp_your"):
        r.ok(f"Token starts with: {token[:8]}…")
    else:
        r.fail("GITHUB_TOKEN is missing or still a placeholder")
    r.duration_ms = (time.monotonic() - t0) * 1000
    results.append(r)

    r = TestResult("GitHub API reachable with token")
    t0 = time.monotonic()
    if not token or token.startswith("ghp_your"):
        r.fail("Skipped — no valid token")
        r.duration_ms = (time.monotonic() - t0) * 1000
        results.append(r)
        return results

    try:
        import urllib.request
        req = urllib.request.Request(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token}",
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            login = data.get("login", "unknown")
            r.ok(f"Authenticated as: {login}")
    except urllib.error.HTTPError as exc:
        r.fail(f"HTTP {exc.code}: {exc.reason}")
    except Exception as exc:
        r.fail(f"{type(exc).__name__}: {exc}")
    r.duration_ms = (time.monotonic() - t0) * 1000
    results.append(r)

    # Verify target repo accessible
    owner = os.getenv("GITHUB_REPO_OWNER", "")
    repo = os.getenv("GITHUB_REPO_NAME", "")
    if owner and repo:
        r = TestResult(f"GitHub repo {owner}/{repo} accessible")
        t0 = time.monotonic()
        try:
            import urllib.request
            req = urllib.request.Request(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers={"Authorization": f"Bearer {token}",
                         "Accept": "application/vnd.github+json"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                r.ok(f"Repo found: {data.get('full_name')} ({data.get('visibility', 'unknown')})")
        except urllib.error.HTTPError as exc:
            r.fail(f"HTTP {exc.code}: {exc.reason}")
        except Exception as exc:
            r.fail(f"{type(exc).__name__}: {exc}")
        r.duration_ms = (time.monotonic() - t0) * 1000
        results.append(r)

    return results


# ── Section 8: Service Bus Connection ─────────────────────────────────────────

def test_service_bus_connection() -> list[TestResult]:
    results: list[TestResult] = []
    conn_str = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING", "")

    r = TestResult("Service Bus connection string present")
    t0 = time.monotonic()
    is_placeholder = (not conn_str
                      or "your-namespace" in conn_str
                      or "your-shared-access-key" in conn_str)
    if not is_placeholder:
        r.ok("Connection string set (non-placeholder)")
    else:
        r.fail("AZURE_SERVICEBUS_CONNECTION_STRING is missing or still a placeholder")
    r.duration_ms = (time.monotonic() - t0) * 1000
    results.append(r)

    r = TestResult("Service Bus SDK importable")
    t0 = time.monotonic()
    try:
        from azure.servicebus import ServiceBusClient  # noqa: F401
        r.ok("azure-servicebus imported successfully")
    except ImportError as exc:
        r.fail(f"ImportError: {exc}")
    r.duration_ms = (time.monotonic() - t0) * 1000
    results.append(r)

    r = TestResult("Service Bus connection attempt")
    t0 = time.monotonic()
    if is_placeholder:
        r.fail("Skipped — no valid connection string")
        r.duration_ms = (time.monotonic() - t0) * 1000
        results.append(r)
        return results

    try:
        from azure.servicebus import ServiceBusClient
        with ServiceBusClient.from_connection_string(conn_str, retry_total=0) as client:
            # A successful context-manager entry confirms the connection string parses
            # and TLS handshake succeeds.
            r.ok("Connected to Service Bus namespace successfully")
    except Exception as exc:
        r.fail(f"{type(exc).__name__}: {exc}")
    r.duration_ms = (time.monotonic() - t0) * 1000
    results.append(r)

    return results


# ── Main ───────────────────────────────────────────────────────────────────────

SECTIONS = [
    ("1. Environment Setup",              test_environment),
    ("2. Azure Services (Service Bus)",   test_azure_services),
    ("3. Agent Imports",                  test_agent_imports),
    ("4. Dashboard",                      test_dashboard),
    ("5. Demo Scenarios",                 test_demo_scenarios),
    ("6. pytest Suite",                   test_pytest_suite),
    ("7. GitHub Connection",              test_github_connection),
    ("8. Service Bus Connection",         test_service_bus_connection),
]


def main():
    started_at = datetime.now(timezone.utc).isoformat()
    print(f"\n{'█' * 60}")
    print(f"  Azure Incident Resolver — System Test")
    print(f"  {started_at}")
    print(f"{'█' * 60}")

    all_results: dict[str, list[TestResult]] = {}
    for section_label, fn in SECTIONS:
        section_results = run_section(section_label, fn)
        all_results[section_label] = section_results

    # ── Summary ───────────────────────────────────────────────────────────────
    total = sum(len(v) for v in all_results.values())
    passed = sum(1 for v in all_results.values() for r in v if r.passed)
    failed = sum(1 for v in all_results.values() for r in v if r.passed is False)
    pct = round(passed / total * 100, 1) if total else 0.0

    print(f"\n{'═' * 60}")
    print(f"  FINAL SUMMARY")
    print(f"{'═' * 60}")
    print(f"  Total tests : {total}")
    print(f"  Passed      : {passed}  ✅")
    print(f"  Failed      : {failed}  {'❌' if failed else '✅'}")
    print(f"  Score       : {pct}%")
    print(f"{'═' * 60}\n")

    # ── JSON report ───────────────────────────────────────────────────────────
    report = {
        "generated_at": started_at,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "percentage": pct,
        },
        "sections": {
            label: [r.to_dict() for r in results]
            for label, results in all_results.items()
        },
    }

    report_path = PROJECT_ROOT / "TEST_RESULTS.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"  📄 Report saved to: {report_path}\n")

    # Exit non-zero if any test failed
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
