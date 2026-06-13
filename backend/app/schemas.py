from pydantic import BaseModel
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    dev = "dev"
    qc = "qc"


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    project_id: str
    user_role: UserRole
    message: str
    history: list[ChatMessage] = []


class UploadResponse(BaseModel):
    status: str
    message: str
    chunks_added: int
    project_id: str
    version: int = 1
    is_new_version: bool = False


class ProjectDoc(BaseModel):
    filename: str
    source: str
    chunks: int


class ProjectInfo(BaseModel):
    project_id: str
    project_name: str
    documents: list[ProjectDoc] = []
    total_chunks: int = 0


class VersionInfo(BaseModel):
    version: int
    filename: str
    uploaded_at: str
    chunks_count: int
    hash: str


class VersionedDoc(BaseModel):
    filename: str
    total_versions: int
    latest_version: int
    latest_uploaded_at: str
    chunks_count: int


class DiffRequest(BaseModel):
    filename: str
    version_a: int
    version_b: int


class DiffResponse(BaseModel):
    project_id: str
    filename: str
    version_old: int
    version_new: int
    analysis: str


# ─────────────────────────────────────────
# Test Generation
# ─────────────────────────────────────────

class TestGenerationRequest(BaseModel):
    endpoint_method: str  # GET, POST, PUT, DELETE
    endpoint_path: str    # /api/v1/projects/upload-doc
    request_body: Optional[dict] = None
    expected_status: int = 200
    description: Optional[str] = None


class TestGenerationResponse(BaseModel):
    test_code: str
    test_file: str
    description: str


class TestResult(BaseModel):
    test_name: str
    status: str  # passed, failed, error
    duration: float
    output: str
    error_message: Optional[str] = None


class TestReport(BaseModel):
    total_tests: int
    passed: int
    failed: int
    errors: int
    total_duration: float
    results: list[TestResult]
    report_html: Optional[str] = None


class JiraBugRequest(BaseModel):
    title: str
    description: str
    test_result: TestResult
    assignee: Optional[str] = None


class JiraBugResponse(BaseModel):
    status: str
    message: str
    ticket_key: Optional[str] = None
    ticket_url: Optional[str] = None


class FullTestWorkflowRequest(BaseModel):
    project_id: str
    endpoint_method: str
    endpoint_path: str
    request_data: Optional[dict] = None
    expected_status: int = 200
    assignee: Optional[str] = None


class FullTestWorkflowResponse(BaseModel):
    status: str
    test_code: str
    test_result: Optional[TestResult] = None
    report: Optional[str] = None
    jira_ticket: Optional[JiraBugResponse] = None


# ─────────────────────────────────────────
# API Spec Parsing
# ─────────────────────────────────────────

class EndpointInfo(BaseModel):
    method: str  # GET, POST, PUT, DELETE
    path: str    # /api/v1/projects/
    summary: Optional[str] = None
    description: Optional[str] = None
    request_body: Optional[dict] = None
    expected_status: int = 200


class ParsedSpecResponse(BaseModel):
    source_file: str
    spec_type: str  # openapi, postman
    total_endpoints: int
    endpoints: list[EndpointInfo]


class BulkTestRequest(BaseModel):
    endpoint_ids: list[str]  # List of endpoint identifiers (method+path)
    run_tests: bool = True   # If True, run tests after generation
    create_bugs: bool = True  # If True, create Jira bugs for failures
    assignee: Optional[str] = None


class BulkTestResponse(BaseModel):
    total_endpoints: int
    tests_generated: int
    tests_run: int
    passed: int
    failed: int
    errors: int
    test_results: list[TestResult]
    jira_tickets: list[JiraBugResponse] = []
    test_codes: dict[str, str] = {}  # endpoint_id -> test_code
