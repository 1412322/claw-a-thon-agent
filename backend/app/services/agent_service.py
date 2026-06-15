from openai import AsyncOpenAI
from app.config import get_settings
from app.database.vector_db import retrieve_context
from app.schemas import ChatMessage, UserRole
from typing import AsyncGenerator

settings = get_settings()

GLOBAL_SYSTEM_PROMPT = """Bạn là Agent Trợ lý Kỹ thuật của Team Tech, hoạt động theo kiến trúc Global Core + Local Project Knowledge.
Nhiệm vụ: hỗ trợ Dev (Lập trình viên) và QC (Kiểm thử viên) dựa trên tài liệu đặc tả dự án được cung cấp.

# QUY TẮC BẮT BUỘC
- Ưu tiên trả lời dựa trên DỮ LIỆU ĐẶC TẢ DỰ ÁN được cung cấp bên dưới.
- Nếu tài liệu không đủ chi tiết, hãy sử dụng kiến thức chung về best practices để bổ sung.
- Khi bổ sung từ kiến thức chung, hãy ghi rõ: "[Best Practice - Không có trong tài liệu]"
- Ngôn ngữ: Tiếng Việt chuyên ngành IT. Văn phong ngắn gọn, trực tiếp.

# CHUẨN ĐẦU RA CHO QC
Khi nhận diện yêu cầu từ QC hoặc liên quan đến kiểm thử:
- LUÔN tạo đầy đủ test cases cho TẤT CẢ scenarios có thể xảy ra
- Định dạng Test Case: Bảng Markdown: | ID | Feature | Scenario | Pre-conditions | Steps | Expected Result | Test Type |
- Test Type: Happy Path / Negative / Edge Case
- Luôn bao gồm đủ 3 nhóm: Happy Path, Negative Path, Edge Cases (timeout, mất kết nối, race condition, invalid input)
- Số lượng test cases: Tùy thuộc độ phức tạp tính năng, không giới hạn số lượng
- **QUAN TRỌNG: Hãy trả lời ĐẦY ĐỦ và CHI TIẾT, không rút gọn. Tiếp tục viết cho đến khi hoàn thành TẤT CẢ test cases.**
- Định dạng Bug Jira: **Title** | **Environment** | **Steps to Reproduce** | **Expected vs Actual** | **Logs**

# CHUẨN ĐẦU RA CHO DEV
Khi nhận diện yêu cầu từ Dev hoặc liên quan đến code:
- Code phải có Exception Handling, logging đầy đủ nhưng không log thông tin nhạy cảm (OTP, password, token)
- Luôn xuất kèm GitLab MR Template:
  ```
  ## Purpose: [Jira Ticket] - Mục đích
  ## Changes: Các file/logic thay đổi
  ## Testing: Hướng dẫn QC test tính năng này
  ## Checklist: [ ] Unit test [ ] Backward compatible
  ```

# CÔNG CỤ & MÔI TRƯỜNG
- Quản lý công việc: Jira | Quản lý code: GitLab | Tài liệu: Confluence, Figma

# DỮ LIỆU ĐẶC TẢ DỰ ÁN
{project_context}"""


def build_system_prompt(project_context: str) -> str:
    if not project_context:
        context_text = "⚠️ Chưa có tài liệu đặc tả nào được nạp cho dự án này. Hãy thông báo cho người dùng upload tài liệu trước."
    else:
        context_text = project_context
    return GLOBAL_SYSTEM_PROMPT.format(project_context=context_text)


def build_role_hint(user_role: UserRole) -> str:
    if user_role == UserRole.qc:
        return "[Người dùng là QC - Ưu tiên định dạng Test Case và Bug Report]\n"
    return "[Người dùng là Dev - Ưu tiên định dạng code và MR Template]\n"


async def stream_chat(
    project_id: str,
    user_role: UserRole,
    message: str,
    history: list[ChatMessage]
) -> AsyncGenerator[str, None]:
    from openai import AsyncOpenAI

    # Create client with longer timeout for long responses
    client = AsyncOpenAI(
        api_key=settings.greenode_api_key,
        base_url="https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1",
        timeout=120.0  # 120 seconds timeout for long responses
    )

    # RAG: retrieve context - increase k for more comprehensive context
    project_context = retrieve_context(query=message, project_id=project_id, k=5)
    print(f"[AgentService] Retrieved {len(project_context)} chars of context")

    system_prompt = build_system_prompt(project_context)
    role_hint = build_role_hint(user_role)

    # Build conversation history (keep last 10 turns for better context)
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    for msg in history[-10:]:
        messages.append({"role": msg.role, "content": msg.content})

    # Add current message with role hint
    messages.append({"role": "user", "content": role_hint + message})

    print(f"[AgentService] Sending request with {len(messages)} messages")
    print(f"[AgentService] Model: {settings.llm_model}")
    print(f"[AgentService] API Key present: {bool(settings.greenode_api_key)}")

    try:
        print(f"[AgentService] Calling Greenode API...")
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.5,
            max_tokens=8192,
            stream=True,
            stream_options={"include_usage": True}
        )

        print(f"[AgentService] Got response, starting to iterate chunks...")
        total_chars = 0
        chunk_count = 0
        last_chunk_time = __import__('time').time()

        async for chunk in response:
            chunk_count += 1
            current_time = __import__('time').time()

            # Check for finish reason to detect premature stopping
            if chunk.choices:
                finish_reason = chunk.choices[0].finish_reason
                if finish_reason:
                    print(f"[AgentService] Stream finished with reason: {finish_reason}")
                    if finish_reason == "length":
                        print("[AgentService] WARNING: Response hit max_tokens limit!")
                    elif finish_reason == "content_filter":
                        print("[AgentService] WARNING: Response was content-filtered!")

                delta_content = chunk.choices[0].delta.content
                if delta_content:
                    total_chars += len(delta_content)
                    last_chunk_time = current_time
                    print(f"[AgentService] Yielding chunk {chunk_count}: {delta_content[:50]}...")
                    yield delta_content

            # Check for usage info in chunk
            if hasattr(chunk, 'usage') and chunk.usage:
                usage = chunk.usage
                print(f"[AgentService] Token usage - prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens}, total: {usage.total_tokens}")

        elapsed = __import__('time').time() - last_chunk_time
        print(f"[AgentService] Stream completed: {chunk_count} chunks, {total_chars} total chars, {elapsed:.1f}s")

    except Exception as e:
        print(f"[AgentService] Error: {e}")
        import traceback
        traceback.print_exc()
        raise
