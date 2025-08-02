# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse

from routes.analyze import router as analyze_router
from routes.helpbot import router as helpbot_router
import os


app = FastAPI()

# ADDED ✅ took out non www site
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.smartquotr.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ CORS Debug Logging Middleware
@app.middleware("http")
async def log_cors_headers(request: Request, call_next):
    response = await call_next(request)
    print("🔁 Origin:", request.headers.get("origin"))
    print("🧾 Access-Control-Allow-Origin:", response.headers.get("access-control-allow-origin"))
    return response

# ADDED ✅ Serve frontend static assets
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

if os.path.isdir("public"):
    app.mount("/public", StaticFiles(directory="public"), name="public")

# ✅ Register routes
app.include_router(analyze_router)
app.include_router(helpbot_router)

# ADDED ✅ Root test endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h1>SmartQuotr Backend is live ✅</h1>"

# ✅ 404 handler (add here)
@app.exception_handler(404)
async def not_found(request, exc):
    return HTMLResponse(content="🚫 Page not found.", status_code=404)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

