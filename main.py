import os
# Prevent XGBoost OpenMP deadlocks
os.environ['KMP_DUPLICATE_LIB_OK'] = "1"
os.environ['OMP_NUM_THREADS'] = "1"

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# Create the FastAPI app
app = FastAPI(title="Market ML: Cloud-Native Market Prediction & Risk Analysis Platform")

# Add CORS Middleware
# Same-origin dashboard: wildcard origins cannot be combined with credentialed
# requests, so credential support stays off.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(ROOT_DIR, "app")
STATIC_DIR = os.path.join(APP_DIR, "static")
TEMPLATES_DIR = os.path.join(APP_DIR, "templates")

# Create directories if they don't exist
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

from app.api_routes import router as api_router
from app.forecast_routes import forecast_router
from app.portfolio_routes import portfolio_router
from app.auth_routes import router as auth_router
from app.ml_routes import router as ml_router

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include the API routes
app.include_router(api_router)
app.include_router(forecast_router)
app.include_router(portfolio_router)
app.include_router(auth_router)
app.include_router(ml_router)

# Setup Jinja2 templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.get("/", response_class=HTMLResponse)
async def serve_frontend(request: Request):
    """Serves the main Market ML single-page application."""
    for path in [
        os.path.join(TEMPLATES_DIR, "index.html"),
        os.path.join(APP_DIR, "index.html"),
        os.path.join(STATIC_DIR, "index.html"),
        os.path.join(ROOT_DIR, "index.html")
    ]:
        if os.path.exists(path):
            return FileResponse(path, media_type="text/html")
    try:
        return templates.TemplateResponse(request=request, name="index.html")
    except Exception:
        return templates.TemplateResponse("index.html", {"request": request})

@app.get("/index.html", response_class=HTMLResponse)
async def serve_index(request: Request):
    return await serve_frontend(request)

@app.get("/style_v3.css")
async def serve_root_css():
    css_path = os.path.join(STATIC_DIR, "style_v3.css")
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css")
    return HTMLResponse(content="", status_code=404)

@app.get("/script_v52.js")
async def serve_root_js():
    js_path = os.path.join(STATIC_DIR, "script_v52.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    return HTMLResponse(content="", status_code=404)

@app.get("/api/health")
@app.get("/health")
async def health_check():
    """Simple API health check."""
    return {"status": "ok", "message": "Market ML FastAPI backend is running"}

@app.get("/favicon.ico")
async def favicon():
    return HTMLResponse(content="", status_code=204)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
