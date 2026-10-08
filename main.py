import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Create the FastAPI app
app = FastAPI(title="Financial Market Prediction API")

# Setup paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(ROOT_DIR, "app")
STATIC_DIR = os.path.join(APP_DIR, "static")
TEMPLATES_DIR = os.path.join(APP_DIR, "templates")

# Create directories if they don't exist
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.get("/", response_class=HTMLResponse)
async def serve_frontend(request: Request):
    """Serves the main HTML single-page application."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health")
async def health_check():
    """Simple API health check."""
    return {"status": "ok", "message": "FastAPI backend is running"}

if __name__ == "__main__":
    import uvicorn
    # Run the uvicorn server on port 8001
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
