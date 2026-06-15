from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from app.api.chat_router import router as chat_router
from app.api.project_router import router as project_router
from app.api.test_router import router as test_router
from app.config import get_settings
import os

settings = get_settings()

app = FastAPI(
    title="Tech Team AI Agent",
    description="AI Co-Pilot cho Dev và QC — Global Core + Local Project Knowledge",
    version="1.0.0-demo"
)


# Global exception handler for non-HTTP exceptions only
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Ensure all non-HTTP exceptions return JSON response."""
    # Don't handle HTTPException - let FastAPI handle it normally
    if isinstance(exc, HTTPException):
        raise exc

    return JSONResponse(
        status_code=500,
        content={"detail": f"Lỗi server: {str(exc)}"}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files path (frontend build output)
STATIC_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

# Define health endpoint FIRST (before any catch-all routes)
@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0-demo"}

# Include API routers
app.include_router(chat_router)
app.include_router(project_router)
app.include_router(test_router)


# Serve frontend for all non-API routes (SPA support)
@app.api_route("/{full_path:path}", methods=["GET"])
async def serve_frontend(full_path: str):
    # Serve index.html for root and SPA routing
    if os.path.exists(STATIC_PATH):
        # Check if it's a static asset (like /assets/...)
        static_file = os.path.join(STATIC_PATH, full_path)
        if os.path.exists(static_file) and os.path.isfile(static_file):
            return FileResponse(static_file)

        # Serve index.html for SPA routing (including root path)
        index_html = os.path.join(STATIC_PATH, "index.html")
        if os.path.exists(index_html):
            return FileResponse(index_html)

    return {"error": "Frontend not found"}, 404


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port="8000", reload=True)
