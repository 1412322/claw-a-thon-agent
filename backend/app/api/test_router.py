"""
Test Router - Endpoints for test generation, execution, and reporting.
"""
import json
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from app.schemas import (
    TestGenerationRequest, TestGenerationResponse,
    TestResult, TestReport, JiraBugRequest, JiraBugResponse,
    FullTestWorkflowRequest, FullTestWorkflowResponse,
    EndpointInfo, ParsedSpecResponse, BulkTestRequest, BulkTestResponse
)
from app.services.test_service import (
    generate_pytest_script,
    run_test_script,
    generate_test_report
)
from app.services.jira_service import jira_service
from app.services.api_parser_service import parse_openapi_spec, parse_postman_collection

router = APIRouter(prefix="/api/v1/test", tags=["test"])


@router.post("/generate", response_model=TestGenerationResponse)
async def generate_test(request: TestGenerationRequest):
    """
    Generate a pytest script for testing an API endpoint.

    Use this endpoint to automatically create test code for any API endpoint.
    The generated test can be saved and run with pytest.
    """
    test_code = generate_pytest_script(
        endpoint_method=request.endpoint_method,
        endpoint_path=request.endpoint_path,
        request_body=request.request_body,
        expected_status=request.expected_status,
        description=request.description
    )

    test_file = f"test_{request.endpoint_path.replace('/', '_').strip('_')}.py"

    return TestGenerationResponse(
        test_code=test_code,
        test_file=test_file,
        description=request.description or f"Test {request.endpoint_method} {request.endpoint_path}"
    )


@router.post("/run", response_model=TestResult)
async def run_test(request: TestGenerationRequest):
    """
    Generate and run a test immediately, returning the result.

    This combines test generation and execution in one call.
    """
    # Generate test code
    test_code = generate_pytest_script(
        endpoint_method=request.endpoint_method,
        endpoint_path=request.endpoint_path,
        request_body=request.request_body,
        expected_status=request.expected_status,
        description=request.description
    )

    # Run the test
    test_name = f"test_{request.endpoint_path.replace('/', '_').strip('_')}"
    result = run_test_script(test_code, test_name)

    return result


@router.post("/create-bug", response_model=JiraBugResponse)
async def create_bug(request: JiraBugRequest):
    """
    Create a Jira bug ticket from a failed test.

    Automatically formats the bug report with test details and assigns to dev.
    If Jira is not configured, returns a mock response with formatted bug details.
    """
    result = jira_service.create_bug(
        title=request.title,
        description=request.description,
        test_result=request.test_result.model_dump(),
        assignee=request.assignee
    )

    return result


@router.post("/run-full-workflow", response_model=FullTestWorkflowResponse)
async def run_full_workflow(request: FullTestWorkflowRequest):
    """
    Complete test workflow: generate test → run → report → create bug if failed.

    This endpoint orchestrates the entire QA automation flow:
    1. Generates pytest script from endpoint info
    2. Runs the test
    3. Generates report
    4. If test failed, creates Jira bug and assigns to dev

    Perfect for CI/CD pipelines or automated regression testing.
    """
    # Step 1: Generate test code
    test_code = generate_pytest_script(
        endpoint_method=request.endpoint_method,
        endpoint_path=request.endpoint_path,
        request_body=request.request_data,
        expected_status=request.expected_status
    )

    test_name = f"test_{request.endpoint_path.replace('/', '_').strip('_')}"

    # Step 2: Run the test
    test_result = run_test_script(test_code, test_name)

    # Step 3: Generate report
    report = generate_test_report([test_result])

    # Step 4: Create bug if failed
    jira_ticket = None
    if test_result.status in ("failed", "error"):
        bug_title = f"API Test Failed: {request.endpoint_method} {request.endpoint_path}"
        bug_description = f"Automated test failed for endpoint {request.endpoint_method} {request.endpoint_path}"

        jira_ticket = jira_service.create_bug(
            title=bug_title,
            description=bug_description,
            test_result=test_result.model_dump(),
            assignee=request.assignee
        )

    return FullTestWorkflowResponse(
        status=test_result.status,
        test_code=test_code,
        test_result=test_result,
        report=report.report_html,
        jira_ticket=jira_ticket
    )


@router.get("/export-postman")
async def export_postman_collection():
    """
    Export all API endpoints as a Postman collection.

    Returns a JSON collection that can be imported into Postman for manual testing.
    """
    collection = {
        "info": {
            "name": "Tech Team AI Agent API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [
            {
                "name": "Projects",
                "item": [
                    {
                        "name": "List Projects",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "http://localhost:8000/api/v1/projects/",
                                "host": ["http", "localhost", "8000"],
                                "path": ["api", "v1", "projects", ""]
                            }
                        }
                    },
                    {
                        "name": "Upload Document",
                        "request": {
                            "method": "POST",
                            "header": [{"key": "Content-Type", "value": "multipart/form-data"}],
                            "body": {
                                "mode": "formdata",
                                "formdata": [
                                    {"key": "file", "type": "file", "src": []},
                                    {"key": "project_id", "value": "my-project"},
                                    {"key": "project_name", "value": "My Project"}
                                ]
                            },
                            "url": {
                                "raw": "http://localhost:8000/api/v1/projects/upload-doc",
                                "host": ["http", "localhost", "8000"],
                                "path": ["api", "v1", "projects", "upload-doc"]
                            }
                        }
                    }
                ]
            },
            {
                "name": "Chat",
                "item": [
                    {
                        "name": "Stream Chat",
                        "request": {
                            "method": "POST",
                            "header": [{"key": "Content-Type", "value": "application/json"}],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "project_id": "my-project",
                                    "user_role": "dev",
                                    "message": "Hello",
                                    "history": []
                                }, indent=2)
                            },
                            "url": {
                                "raw": "http://localhost:8000/api/v1/chat/stream",
                                "host": ["http", "localhost", "8000"],
                                "path": ["api", "v1", "chat", "stream"]
                            }
                        }
                    }
                ]
            },
            {
                "name": "Test Automation",
                "item": [
                    {
                        "name": "Generate Test",
                        "request": {
                            "method": "POST",
                            "header": [{"key": "Content-Type", "value": "application/json"}],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "endpoint_method": "GET",
                                    "endpoint_path": "/api/v1/projects/",
                                    "expected_status": 200
                                }, indent=2)
                            },
                            "url": {
                                "raw": "http://localhost:8000/api/v1/test/generate",
                                "host": ["http", "localhost", "8000"],
                                "path": ["api", "v1", "test", "generate"]
                            }
                        }
                    },
                    {
                        "name": "Run Full Workflow",
                        "request": {
                            "method": "POST",
                            "header": [{"key": "Content-Type", "value": "application/json"}],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "project_id": "my-project",
                                    "endpoint_method": "GET",
                                    "endpoint_path": "/api/v1/projects/",
                                    "expected_status": 200,
                                    "assignee": "dev-username"
                                }, indent=2)
                            },
                            "url": {
                                "raw": "http://localhost:8000/api/v1/test/run-full-workflow",
                                "host": ["http", "localhost", "8000"],
                                "path": ["api", "v1", "test", "run-full-workflow"]
                            }
                        }
                    }
                ]
            }
        ]
    }

    return collection


# ─────────────────────────────────────────
# API Spec Upload & Parsing
# ─────────────────────────────────────────

@router.post("/upload-spec", response_model=ParsedSpecResponse)
async def upload_spec(file: UploadFile = File(...)):
    """
    Upload Swagger/OpenAPI spec or Postman collection.

    Accepts:
    - OpenAPI 2.0/3.0 spec (JSON or YAML)
    - Postman collection v2.0/v2.1 (JSON)

    Returns parsed list of endpoints.
    """
    contents = await file.read()
    filename = file.filename or ""

    # Detect file type
    if filename.lower().endswith(('.json', '.yaml', '.yml')):
        openapi_error = None
        postman_error = None

        try:
            # Try OpenAPI first
            return parse_openapi_spec(contents)
        except ValueError as e:
            openapi_error = str(e)
            pass

        try:
            # Try Postman
            return parse_postman_collection(contents)
        except ValueError as e:
            postman_error = str(e)
            raise HTTPException(
                status_code=400,
                detail=f"File is not a valid OpenAPI spec or Postman collection. OpenAPI error: {openapi_error}. Postman error: {postman_error}"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use .json, .yaml, or .yml"
        )


# ─────────────────────────────────────────
# Bulk Test Operations
# ─────────────────────────────────────────

@router.post("/bulk-generate", response_model=BulkTestResponse)
async def bulk_generate_tests(request: BulkTestRequest):
    """
    Generate tests for multiple endpoints at once.

    Args:
        endpoint_ids: List of endpoint identifiers (e.g., ["GET:/api/v1/projects/:List Projects", "POST:/api/v1/chat/stream/:Stream Chat"])
        run_tests: If True, also run the generated tests

    Returns:
        BulkTestResponse with all test codes and optional results
    """
    test_codes = {}
    test_results = []
    jira_tickets = []

    for endpoint_id in request.endpoint_ids:
        # Parse endpoint_id (format: "METHOD:path[:summary]")
        try:
            parts = endpoint_id.rsplit(':', 2)
            method = parts[0]
            path = parts[1] if len(parts) > 1 else ''
            summary = parts[2] if len(parts) > 2 else None
        except ValueError:
            continue

        # Generate test with summary for better test name
        test_code = generate_pytest_script(
            endpoint_method=method,
            endpoint_path=path,
            expected_status=200,
            summary=summary
        )

        test_name = f"test_{path.replace('/', '_').strip('_')}"
        test_codes[endpoint_id] = test_code

        # Optionally run test
        if request.run_tests:
            result = run_test_script(test_code, test_name)
            test_results.append(result)

            # Create bug if failed
            if request.create_bugs and result.status in ("failed", "error"):
                ticket = jira_service.create_bug(
                    title=f"API Test Failed: {method} {path}",
                    description=f"Automated test failed for {method} {path}",
                    test_result=result.model_dump(),
                    assignee=request.assignee
                )
                jira_tickets.append(ticket)

    return BulkTestResponse(
        total_endpoints=len(request.endpoint_ids),
        tests_generated=len(test_codes),
        tests_run=len(test_results),
        passed=sum(1 for r in test_results if r.status == "passed"),
        failed=sum(1 for r in test_results if r.status == "failed"),
        errors=sum(1 for r in test_results if r.status == "error"),
        test_results=test_results,
        jira_tickets=jira_tickets,
        test_codes=test_codes
    )


@router.post("/bulk-run", response_model=BulkTestResponse)
async def bulk_run_tests(request: BulkTestRequest):
    """
    Run tests for multiple endpoints (shorthand for bulk-generate with run_tests=True).
    """
    request.run_tests = True
    return await bulk_generate_tests(request)
