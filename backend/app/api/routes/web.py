"""Web UI Dashboard route — renders modern SPA interface for manual lead discovery."""

from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["web"])

TEMPLATE_PATH = Path(__file__).resolve().parent.parent.parent / "templates" / "index.html"


@router.get("/", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the interactive SALEP Sales Intelligence Web UI."""
    if TEMPLATE_PATH.exists():
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        return HTMLResponse(content=content)
    return HTMLResponse(
        content="<h1>SALEP Dashboard</h1><p>Template not found at app/templates/index.html</p>",
        status_code=500,
    )
