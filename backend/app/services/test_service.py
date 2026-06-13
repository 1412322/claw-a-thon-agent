"""
Test Service - Generate, run pytest scripts and create reports.
"""
import tempfile
import subprocess
import os
import re
from pathlib import Path
from typing import Optional
from app.config import get_settings
from app.schemas import TestResult, TestReport

settings = get_settings()


def generate_pytest_script(
    endpoint_method: str,
    endpoint_path: str,
    request_body: Optional[dict] = None,
    expected_status: int = 200,
    description: Optional[str] = None,
    summary: Optional[str] = None
) -> str:
    """
    Generate a pytest script for testing an API endpoint.
    """
    import re
    method_upper = endpoint_method.upper()

    # Use summary for test name if available, otherwise use path
    if summary:
        # Sanitize summary for Python identifier
        clean_name = re.sub(r'[^a-zA-Z0-9]', '_', summary).strip('_')
        test_name = f"test_{clean_name}" if clean_name else "test_api_endpoint"
    else:
        # Fallback to path-based name
        clean_path = endpoint_path
        clean_path = re.sub(r'^https?://', '', clean_path)
        clean_path = re.sub(r'^[^/]+', '', clean_path)
        clean_path = clean_path.split('?')[0]
        clean_path = re.sub(r'[^a-zA-Z0-9]', '_', clean_path).strip('_')
        test_name = f"test_{clean_path}" if clean_path else "test_api_endpoint"

    # For external URLs, use httpx instead of TestClient
    is_external_url = '://' in endpoint_path

    if is_external_url:
        # External API test - no duplicate imports
        if method_upper in ["POST", "PUT", "PATCH"]:
            if request_body:
                body_json = str(request_body).replace("'", '"')
                test_code = f"""import pytest
import httpx


async def {test_name}():
    \"\"\"
    {description or f'Test {method_upper} {endpoint_path}'}
    \"\"\"
    async with httpx.AsyncClient() as client:
        response = await client.{method_upper.lower()}(
            "{endpoint_path}",
            json={body_json}
        )

    assert response.status_code == {expected_status}, f"Expected {{ {expected_status} }}, got {{ response.status_code }}: {{ response.text }}"
"""
            else:
                test_code = f"""import pytest
import httpx


async def {test_name}():
    \"\"\"
    {description or f'Test {method_upper} {endpoint_path}'}
    \"\"\"
    async with httpx.AsyncClient() as client:
        response = await client.{method_upper.lower()}(
            "{endpoint_path}",
            json={{"}}
        )

    assert response.status_code == {expected_status}, f"Expected {{ {expected_status} }}, got {{ response.status_code }}: {{ response.text }}"
"""
        else:
            test_code = f"""import pytest
import httpx


async def {test_name}():
    \"\"\"
    {description or f'Test {method_upper} {endpoint_path}'}
    \"\"\"
    async with httpx.AsyncClient() as client:
        response = await client.{method_upper.lower()}(
            "{endpoint_path}"
        )

    assert response.status_code == {expected_status}, f"Expected {{ {expected_status} }}, got {{ response.status_code }}: {{ response.text }}"
"""
    else:
        # Local API test using TestClient
        if method_upper in ["POST", "PUT", "PATCH"]:
            if request_body:
                body_json = str(request_body).replace("'", '"')
                test_code = f"""import pytest
from fastapi.testclient import TestClient
from app.main import app


def {test_name}():
    \"\"\"
    {description or f'Test {method_upper} {endpoint_path}'}
    \"\"\"
    client = TestClient(app)

    response = client.{method_upper.lower()}(
        "{endpoint_path}",
        json={body_json}
    )

    print(f"\\n=== Response Status: {{response.status_code}} ===")
    print(f"=== Response Body: {{response.text}} ===\\n")

    assert response.status_code == {expected_status}, f"Expected {{ {expected_status} }}, got {{ response.status_code }}: {{ response.text }}"

    if {expected_status} == 200:
        try:
            data = response.json()
            assert data is not None, "Response body should not be empty"
        except:
            pass  # Response might not be JSON
"""
            else:
                test_code = f"""import pytest
from fastapi.testclient import TestClient
from app.main import app


def {test_name}():
    \"\"\"
    {description or f'Test {method_upper} {endpoint_path}'}
    \"\"\"
    client = TestClient(app)

    response = client.{method_upper.lower()}(
        "{endpoint_path}",
        json={{"}}
    )

    print(f"\\n=== Response Status: {{response.status_code}} ===")
    print(f"=== Response Body: {{response.text}} ===\\n")

    assert response.status_code == {expected_status}, f"Expected {{ {expected_status} }}, got {{ response.status_code }}: {{ response.text }}"

    if {expected_status} == 200:
        try:
            data = response.json()
            assert data is not None, "Response body should not be empty"
        except:
            pass  # Response might not be JSON
"""
        else:
            test_code = f"""import pytest
from fastapi.testclient import TestClient
from app.main import app


def {test_name}():
    \"\"\"
    {description or f'Test {method_upper} {endpoint_path}'}
    \"\"\"
    client = TestClient(app)

    response = client.{method_upper.lower()}(
        "{endpoint_path}"
    )

    print(f"\\n=== Response Status: {{response.status_code}} ===")
    print(f"=== Response Body: {{response.text}} ===\\n")

    assert response.status_code == {expected_status}, f"Expected {{ {expected_status} }}, got {{ response.status_code }}: {{ response.text }}"

    if {expected_status} == 200:
        try:
            data = response.json()
            assert data is not None, "Response body should not be empty"
        except:
            pass  # Response might not be JSON
"""
    return test_code


def run_test_script(test_code: str, test_name: str = "test_api") -> TestResult:
    """
    Run a pytest script dynamically and return results.
    """
    import time
    import sys

    start_time = time.time()
    # Use the current working directory (backend in container)
    backend_dir = os.getcwd()

    # Sanitize test_name for filename (remove invalid chars)
    safe_test_name = re.sub(r'[^a-zA-Z0-9_]', '_', test_name)

    # Create temp directory and file
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / f"{safe_test_name}.py"
        test_file.write_text(test_code)

        # Run pytest with PYTHONPATH set
        env = os.environ.copy()
        env["PYTHONPATH"] = backend_dir

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "-v", "-s", "--tb=short"],
                cwd=backend_dir,
                capture_output=True,
                text=True,
                timeout=60,
                env=env
            )

            duration = time.time() - start_time

            # Parse pytest output
            status = "passed" if result.returncode == 0 else "failed"
            output = result.stdout + "\n" + result.stderr

            error_message = None
            if result.returncode != 0:
                # Extract error message
                error_match = re.search(r'FAILED.*?-(.*)', output, re.DOTALL)
                if error_match:
                    error_message = error_match.group(1).strip()[:500]

            return TestResult(
                test_name=test_name,
                status=status,
                duration=duration,
                output=output[:2000],
                error_message=error_message
            )

        except subprocess.TimeoutExpired:
            return TestResult(
                test_name=test_name,
                status="error",
                duration=60.0,
                output="Test timed out after 60 seconds",
                error_message="Timeout"
            )
        except Exception as e:
            return TestResult(
                test_name=test_name,
                status="error",
                duration=time.time() - start_time,
                output=str(e),
                error_message=str(e)
            )


def generate_test_report(results: list[TestResult]) -> TestReport:
    """
    Generate a test report from multiple test results.
    """
    total_duration = sum(r.duration for r in results)
    passed = sum(1 for r in results if r.status == "passed")
    failed = sum(1 for r in results if r.status == "failed")
    errors = sum(1 for r in results if r.status == "error")

    # Generate HTML report
    html_report = generate_html_report(results)

    return TestReport(
        total_tests=len(results),
        passed=passed,
        failed=failed,
        errors=errors,
        total_duration=total_duration,
        results=results,
        report_html=html_report
    )


def generate_html_report(results: list[TestResult]) -> str:
    """
    Generate a simple HTML report for test results.
    """
    total = len(results)
    passed = sum(1 for r in results if r.status == "passed")
    failed = sum(1 for r in results if r.status == "failed")
    errors = sum(1 for r in results if r.status == "error")

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .test {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
        .passed {{ border-color: #4caf50; background: #e8f5e9; }}
        .failed {{ border-color: #f44336; background: #ffebee; }}
        .error {{ border-color: #ff9800; background: #fff3e0; }}
        .status {{ font-weight: bold; }}
        .passed .status {{ color: #4caf50; }}
        .failed .status {{ color: #f44336; }}
        .error .status {{ color: #ff9800; }}
        pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>API Test Report</h1>

    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total:</strong> {total} |
           <span style="color: #4caf50">Passed: {passed}</span> |
           <span style="color: #f44336">Failed: {failed}</span> |
           <span style="color: #ff9800">Errors: {errors}</span></p>
        <p><strong>Total Duration:</strong> {sum(r.duration for r in results):.2f}s</p>
    </div>

    <h2>Test Results</h2>
"""

    for result in results:
        status_class = result.status
        status_text = result.status.upper()
        html += f"""
    <div class="test {status_class}">
        <h3>{result.test_name}</h3>
        <p><span class="status">{status_text}</span> - {result.duration:.2f}s</p>
        {f'<p><strong>Error:</strong> {result.error_message}</p>' if result.error_message else ''}
        <pre>{result.output[:500]}...</pre>
    </div>
"""

    html += """
</body>
</html>
"""
    return html
