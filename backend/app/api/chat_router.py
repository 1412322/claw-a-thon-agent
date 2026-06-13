from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas import ChatRequest
from app.services.agent_service import stream_chat
import json

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/stream")
async def chat_stream(payload: ChatRequest):
    """Stream chat response as Server-Sent Events."""

    async def event_generator():
        try:
            async for chunk in stream_chat(
                project_id=payload.project_id,
                user_role=payload.user_role,
                message=payload.message,
                history=payload.history
            ):
                # SSE format: data: <json>\n\n
                data = json.dumps({"text": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"

            # Signal stream end
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
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
