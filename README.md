# 🤖 Tech Team AI Agent — Demo v2.0

AI Co-Pilot cho Dev và QC với kiến trúc **Global Core + Local Project Knowledge**. Hỗ trợ chat với tài liệu, tự động hóa test API, và phân tích diff tài liệu.

---

## ⚡ Quick Start

### 1. Lấy API Key

**Greenode (VNG Cloud) - Recommended:**
```bash
# Đăng ký tại VNG Cloud và lấy API Key
```

**Hoặc dùng OpenAI:**
```bash
# Dùng OPENAI_API_KEY nếu không có Greenode
```

### 2. Cấu hình
```bash
cp backend/.env.example backend/.env
# Mở backend/.env và điền API_KEY
```

### 3. Chạy
```bash
chmod +x start.sh
bash start.sh
```

Mở trình duyệt: **http://localhost:5173**

---

## 🏗️ Kiến trúc

```
┌─────────────────────────────────────────────────────────┐
│              React Frontend                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Chat       │  │  API Testing │  │   Admin      │   │
│  │   Portal     │  │   Portal     │  │   Portal     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP / SSE Stream
┌──────────────────▼──────────────────────────────────────┐
│            FastAPI Backend                               │
│                                                          │
│  /api/v1/chat/stream     - Chat với tài liệu (RAG)      │
│  /api/v1/projects/       - Quản lý project & tài liệu   │
│  /api/v1/test/           - Test automation & reporting  │
│  /api/v1/projects/diff   - Phân tích diff tài liệu      │
└──────────────────┬──────────────────────────────────────┘
                   │
       ┌───────────┴───────────┬────────────────┐
       ▼                       ▼                ▼
┌─────────────┐         ┌─────────────┐  ┌──────────┐
│  ChromaDB   │         │  Greenode   │  │  Jira    │
│  (RAG +     │────────▶│  LLM        │  │  API     │
│  Metadata   │ context │  (VNG)      │  │  (Bug)   │
│  Filter)    │         └─────────────┘  └──────────┘
└─────────────┘
```

**Luồng xử lý mỗi câu hỏi:**
1. User chọn Project + Role (QC/Dev) → gõ câu hỏi
2. Backend nhận `project_id` → query ChromaDB với metadata filter (top 3 chunks)
3. Ghép: System Prompt + Context (~500-800 tokens) + Câu hỏi → gửi LLM
4. Stream response về FE từng token

---

## ✨ Tính năng

### 💬 Chat với Tài liệu (RAG)

| Tính năng | Mô tả |
|-----------|-------|
| **Multi-project** | Hỗ trợ nhiều dự án, mỗi project có kho tài liệu riêng |
| **Role-based** | QC: Test Case, Bug Report \| Dev: Code, MR Template |
| **Metadata Isolation** | Mỗi project chỉ truy xuất đúng tài liệu của project đó |
| **Conversation History** | Lưu 5 lượt hội thoại gần nhất cho context |
| **SSE Streaming** | Response được stream về real-time |

**Định dạng đầu ra chuẩn:**
- **QC:** Bảng Test Case Markdown, Bug Report Jira format
- **Dev:** Code có exception handling + logging, GitLab MR Template

---

### 🧪 API Test Automation

| Tính năng | Mô tả |
|-----------|-------|
| **Spec Parsing** | Upload OpenAPI/Swagger hoặc Postman Collection |
| **Auto Test Generation** | Tự động tạo pytest script cho từng endpoint |
| **Bulk Test Execution** | Chạy hàng loạt tests song song |
| **Jira Integration** | Tự động tạo bug ticket khi test fail |
| **HTML Reports** | Báo cáo test với summary chi tiết |

**Luồng tự động hóa:**
```
Upload Spec → Parse Endpoints → Generate Tests → Run Tests → 
    ↓ (nếu fail)
Create Jira Bug → Assign to Dev
```

**Hỗ trợ:**
- GET, POST, PUT, DELETE, PATCH
- Local API (TestClient) và External API (httpx)
- Request body từ spec example

---

### 📊 Version Control & Diff Analysis

| Tính năng | Mô tả |
|-----------|-------|
| **Version History** | Tự động lưu mỗi lần upload tài liệu mới |
| **Duplicate Detection** | Không lưu version nếu content không đổi |
| **Smart Diff** | LLM phân tích tác động thay đổi |
| **Impact Analysis** | Đề xuất test case cần cập nhật, code cần sửa |

**Diff Analysis trả về:**
- Tóm tắt thay đổi
- Requirement mới / cập nhật / xóa
- Ảnh hưởng đến QC (test case)
- Ảnh hưởng đến Dev (API, logic, config)

---

## 📁 Cấu trúc project

```
agent-demo/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── config.py                  # Settings từ .env
│   │   ├── schemas.py                 # Pydantic models
│   │   ├── api/
│   │   │   ├── chat_router.py         # POST /chat/stream (SSE)
│   │   │   ├── project_router.py      # Upload doc, list projects, diff
│   │   │   └── test_router.py         # Test automation endpoints
│   │   ├── services/
│   │   │   ├── agent_service.py       # LLM + System Prompt + RAG
│   │   │   ├── api_parser_service.py  # Parse OpenAPI/Postman
│   │   │   ├── diff_service.py        # Analyze doc diff
│   │   │   ├── jira_service.py        # Create bug tickets
│   │   │   └── test_service.py        # Generate & run pytest
│   │   └── database/
│   │       ├── vector_db.py           # ChromaDB operations
│   │       └── version_store.py       # Document versioning
│   ├── chroma_db/                     # Vector DB storage
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   └── src/
│       ├── App.jsx                    # Main app + tab switcher
│       ├── store/
│       │   └── globalContext.jsx      # Global state (project, role)
│       ├── services/
│       │   └── api.js                 # Fetch + SSE streaming
│       └── components/
│           ├── Chat/
│           │   ├── ChatWindow.jsx     # Main chat UI
│           │   ├── MessageBubble.jsx  # Markdown render + copy
│           │   ├── QuickPrompts.jsx   # Shortcut buttons
│           │   └── Sidebar.jsx        # Project list + role switcher
│           ├── Admin/
│           │   └── AdminPortal.jsx    # Upload tài liệu
│           └── APITesting.jsx         # Test automation UI
│
├── docs/                              # Tài liệu dự án
├── sample-openapi.json                # Sample OpenAPI spec
├── sample-postman.json                # Sample Postman collection
├── echo.postman_collection.json       # Postman collection for API
├── API_TESTING_GUIDE.md               # Hướng dẫn test API
└── start.sh                           # One-command startup
```

---

## 🎯 Cách dùng

### Bước 1: Tạo dự án và upload tài liệu

1. Click **"Thêm dự án"** ở sidebar
2. Điền mã dự án (ví dụ: `fintech`) và tên hiển thị
3. Upload file BRD/SRS/API Spec (PDF, DOCX, MD, JSON đều được)
4. Chờ xử lý xong → Click **"Bắt đầu chat ngay"**

### Bước 2: Chat với Agent

**Với role QC:**
- Click tab **QC** ở sidebar
- Dùng Quick Prompt **"Viết Test Case"** → điền tên tính năng
- Agent trả ra bảng Jira format với đủ Happy/Negative/Edge case

**Với role Dev:**
- Click tab **Dev** ở sidebar
- Dùng Quick Prompt **"Tạo MR Template"** → mô tả tính năng
- Agent trả ra MR description đúng chuẩn GitLab

### Bước 3: API Testing

1. Chuyển sang tab **🧪 API Testing**
2. Upload OpenAPI spec hoặc Postman collection
3. Chọn endpoints cần test
4. Click **"Run Tests"** để tự động chạy
5. Xem kết quả + Jira tickets (nếu có fail)

### Bước 4: Phân tích Diff

1. Upload lại tài liệu đã có (version mới)
2. Xem **Version History** trong sidebar
3. Chọn 2 versions để so sánh
4. Agent phân tích tác động và đề xuất hành động

---

## 🔧 API Endpoints

### Chat & Projects

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/v1/chat/stream` | Stream chat với tài liệu |
| GET | `/api/v1/projects/` | List tất cả projects |
| POST | `/api/v1/projects/upload-doc` | Upload tài liệu mới |
| GET | `/api/v1/projects/{id}/versions` | Version history của file |
| POST | `/api/v1/projects/{id}/diff` | Phân tích diff 2 versions |

### Test Automation

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/v1/test/upload-spec` | Upload OpenAPI/Postman |
| POST | `/api/v1/test/generate` | Generate pytest script |
| POST | `/api/v1/test/run` | Chạy test ngay |
| POST | `/api/v1/test/bulk-run` | Chạy hàng loạt tests |
| POST | `/api/v1/test/create-bug` | Tạo Jira bug ticket |
| POST | `/api/v1/test/run-full-workflow` | Full flow: test → report → bug |
| GET | `/api/v1/test/export-postman` | Export API collection |

---

## 🔧 Cấu hình nâng cao

### Thay đổi LLM model

Trong `backend/.env`:
```bash
LLM_MODEL=gpt-4o           # Hoặc qwen-max, claude-3-sonnet
GREENODE_API_KEY=your_key  # VNG Cloud Greenode
# HOẶC
OPENAI_API_KEY=your_key    # OpenAI
```

### Tuning RAG

Trong `backend/app/database/vector_db.py`:
```python
chunk_size=800    # Tăng nếu tài liệu cần nhiều context hơn
chunk_overlap=150 # Tăng nếu bị mất thông tin ở ranh giới chunk
k=3               # Số chunks retrieve mỗi query (mặc định 3)
```

### Cấu hình Jira Integration

Trong `backend/.env`:
```bash
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your.email@company.com
JIRA_API_TOKEN=your_api_token
JIRA_DEFAULT_PROJECT=PROJ
JIRA_DEFAULT_ASSIGNEE=dev-username
```

**Lưu ý:**
- `JIRA_DEFAULT_PROJECT`: Project key trong Jira (ví dụ: `PROJ`, `DEMO`, `QA`)
- `JIRA_API_TOKEN`: Tạo tại https://id.atlassian.com/manage-api-tokens
- Nếu không config, Jira service chạy chế độ **mock** (in ra log thay vì tạo ticket thật)

**Troubleshooting:**
- Lỗi 400: Kiểm tra project key có đúng không, hoặc user có permission tạo issue không
- Lỗi 401: Kiểm tra API token và email có đúng không
- Xem log backend để debug payload gửi đi

### Thêm loại file hỗ trợ

Trong `backend/app/api/project_router.py`:
```python
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "md", "txt", "json", "yaml", "yml"}
```

---

## 🔄 Luồng xử lý chi tiết

### Chat Flow
```
User Input → Extract project_id + role
    ↓
Query ChromaDB (metadata filter + top-k similarity)
    ↓
Build prompt: System + Context + Role Hint + Message
    ↓
Stream to LLM (Greenode/OpenAI)
    ↓
SSE → Frontend → Render Markdown
```

### Test Automation Flow
```
Upload Spec → Parse (OpenAPI/Postman) → Extract Endpoints
    ↓
Select Endpoints → Generate pytest scripts
    ↓
Run pytest (subprocess) → Capture output
    ↓
Generate Report (HTML) → If failed → Create Jira Bug
```

### Diff Analysis Flow
```
Upload Doc → Extract Text → Check Hash
    ↓ (nếu khác version cũ)
Save New Version → Update Vector DB
    ↓ (khi user request diff)
Load 2 Versions → Build Diff Prompt → LLM Analysis
    ↓
Return: Summary + Impact on QC/Dev
```

---

## ❓ FAQ

**Q: Agent trả lời sai hoặc không biết?**
A: Kiểm tra tài liệu đã upload chưa (xem số chunks trong sidebar). Nếu có, thử hỏi lại với từ khóa cụ thể hơn có trong tài liệu.

**Q: Tài liệu công ty có bị gửi ra ngoài không?**
A: Tài liệu được lưu local trong ChromaDB trên máy của bạn. Chỉ có các đoạn liên quan (~500 tokens) được gửi kèm mỗi câu hỏi đến LLM API. Không có dữ liệu nào được dùng để training model.

**Q: Muốn reset toàn bộ data?**
A: Xóa thư mục `backend/chroma_db/` và restart backend.

**Q: Jira integration không hoạt động?**
A: Kiểm tra các biến môi trường JIRA_*. Nếu không config, service chạy chế độ mock (in log thay vì tạo ticket thật).

**Q: Test API fail ngay cả khi endpoint đúng?**
A: Kiểm tra:
- Backend API có chạy không (http://localhost:8000/health)
- Request body có khớp với API expectation không
- External API cần có network access

**Q: Chạy production thì cần làm gì thêm?**
A: Phase 1 là demo — cần thêm:
- Authentication (JWT/OAuth)
- Persistent database (PostgreSQL thay vì file-based version store)
- Deploy lên server với proper CORS
- Rate limiting và input validation
- Logging và monitoring

---

## 📋 Tech Stack

| Layer | Tech |
|-------|------|
| **LLM** | Greenode (VNG Cloud) / OpenAI |
| **Vector DB** | ChromaDB (local) |
| **Embeddings** | LLM built-in embeddings |
| **Backend** | FastAPI + Python 3.11+ |
| **Frontend** | React 18 + Tailwind CSS v3 |
| **Streaming** | Server-Sent Events (SSE) |
| **Doc parsing** | PyPDF, python-docx, LangChain |
| **Testing** | pytest, httpx |
| **Integration** | Jira API v3 |

---

## 📝 Changelog

### v2.0 (Current)
- ✅ API Test Automation (OpenAPI/Postman parsing)
- ✅ Bulk test execution với pytest
- ✅ Jira bug ticket integration
- ✅ Document versioning system
- ✅ AI-powered diff analysis
- ✅ Multi-tab UI (Chat + API Testing)

### v1.0
- ✅ Basic RAG chat với ChromaDB
- ✅ Multi-project support với metadata isolation
- ✅ Role-based responses (QC/Dev)
- ✅ SSE streaming
- ✅ Admin portal để upload tài liệu

---

## 📄 License

Internal use only. Demo project for Tech Team AI Agent.
