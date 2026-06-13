# API Testing Guide

## 🎯 Overview

This feature allows you to upload Swagger/OpenAPI specs or Postman collections, parse all endpoints, and automatically generate + run tests with Jira bug creation for failures.

## 📁 File Locations

- **Backend API**: `http://localhost:8000/docs` (Swagger UI)
- **Frontend UI**: Tab switcher at top of screen (Chat ↔ API Testing)
- **Sample spec**: `sample-openapi.json` (for testing)

## 🚀 Quick Start

### 1. Start the Backend

```bash
cd backend
venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start the Frontend

```bash
cd frontend
npm run dev
```

### 3. Open Browser

Go to `http://localhost:5173` and click **"API Testing"** tab

## 📤 Upload API Spec

### Supported Formats

1. **OpenAPI/Swagger** (JSON or YAML)
   - OpenAPI 2.0 (Swagger)
   - OpenAPI 3.0/3.1

2. **Postman Collection** (JSON)
   - Collection v2.0
   - Collection v2.1

### How to Upload

1. Click "API Testing" tab
2. Click "Choose File" button
3. Select your `.json` or `.yaml` file
4. Wait for parsing (endpoints will appear in table)

## 🧪 Run Tests

### Option 1: Generate Only

1. Select endpoints (checkboxes)
2. Click "Generate Tests"
3. View generated pytest code

### Option 2: Run Tests

1. Select endpoints
2. Click "Run Tests"
3. View results (passed/failed/errors)
4. Jira bugs auto-created for failures

### Option 3: Bulk Run

1. Click "Select All"
2. Click "Run Tests"
3. All endpoints tested automatically

## 🐛 Jira Integration

### Configure Jira

Add to `backend/.env`:

```env
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your.email@company.com
JIRA_API_TOKEN=your_api_token
JIRA_DEFAULT_PROJECT=PROJ
JIRA_DEFAULT_ASSIGNEE=dev-username
```

### Auto Bug Creation

When tests fail:
1. Bug ticket auto-created in Jira
2. Includes test details, error messages, logs
3. Assigned to specified developer
4. Link displayed in results

### Mock Mode

If Jira not configured, bug details printed to console with format ready for manual creation.

## 🔧 API Endpoints

### Upload Spec

```bash
POST /api/v1/test/upload-spec
Content-Type: multipart/form-data

Body: file (OpenAPI/Postman JSON/YAML)
```

### Bulk Generate

```bash
POST /api/v1/test/bulk-generate
Content-Type: application/json

{
  "endpoint_ids": ["GET:/api/v1/projects/", "POST:/health"],
  "run_tests": false
}
```

### Bulk Run

```bash
POST /api/v1/test/bulk-run
Content-Type: application/json

{
  "endpoint_ids": ["GET:/api/v1/projects/", "POST:/health"],
  "run_tests": true,
  "create_bugs": true,
  "assignee": "dev-username"
}
```

## 📊 Test Results

Results include:
- **Summary**: Total, Generated, Passed, Failed, Errors
- **Details**: Per-test status, duration, error messages
- **Output**: Full pytest output (expandable)
- **Jira Tickets**: Links to created bug tickets

## 🛠️ Troubleshooting

### "Failed to parse spec file"

- Check file is valid JSON/YAML
- Verify it's OpenAPI or Postman format
- Try with `sample-openapi.json` first

### "Test failed" with import error

- Backend server must be running
- Tests import from `app.main`
- Check backend logs for details

### Jira bugs not created

- Check `.env` has Jira credentials
- Verify API token is valid
- Check backend console for mock output

## 📝 Example Workflow

1. **Upload** `sample-openapi.json`
2. **Select** all 5 endpoints
3. **Click** "Run Tests"
4. **View** results:
   - ✅ Passed: /health, /api/v1/projects/
   - ❌ Failed: /api/v1/projects/upload-doc (needs file)
5. **Check** Jira for auto-created bug

## 🎨 UI Features

- **Tab Switcher**: Toggle between Chat and API Testing
- **File Upload**: Drag & drop or click to select
- **Endpoint Table**: Checkboxes, method badges, path display
- **Bulk Actions**: Select All, Generate, Run
- **Results Panel**: Summary cards, detailed test output
- **Jira Links**: Direct links to created tickets

## 🔒 Security

- API specs parsed locally (not sent to external services)
- Tests run in isolated temp directories
- Jira credentials stored in `.env` (not committed)
- No sensitive data in test output
