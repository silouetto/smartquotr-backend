# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from routes.analyze import router as analyze_router
from routes.helpbot import router as helpbot_router
import os

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.smartquotr.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving
# - took them out
# app.mount("/public", StaticFiles(directory="public"), name="public")
# app.mount("/public/static", StaticFiles(directory="static"), name="static")

# Load analyze routes
app.include_router(analyze_router)

# Load helpbot
app.include_router(helpbot_router)

# ✅ 404 handler (add here)
@app.exception_handler(404)
async def not_found(request, exc):
    return HTMLResponse(content="🚫 Page not found.", status_code=404)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

