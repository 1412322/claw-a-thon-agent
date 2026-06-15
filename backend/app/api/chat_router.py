from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas import ChatRequest
from app.services.agent_service import stream_chat
import json

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/stream")
async def chat_stream(payload: ChatRequest):
    """Stream chat response as Server-Sent Events."""
    print(f"[ChatRouter] Received request: project_id={payload.project_id}, message={payload.message[:50]}...")

    async def event_generator():
        total_yielded = 0
        try:
            print(f"[ChatRouter] Starting stream_chat generator")
            async for chunk in stream_chat(
                project_id=payload.project_id,
                user_role=payload.user_role,
                message=payload.message,
                history=payload.history
            ):
                # SSE format: data: <json>\n\n
                data = json.dumps({"text": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"
                total_yielded += 1
                if total_yielded <= 3:
                    print(f"[ChatRouter] Yielded chunk {total_yielded}: {chunk[:50]}...")

            print(f"[ChatRouter] Stream completed, total chunks yielded: {total_yielded}")
            # Signal stream end
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            print(f"[ChatRouter] Error in event_generator: {e}")
            import traceback
            traceback.print_exc()
            error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )
