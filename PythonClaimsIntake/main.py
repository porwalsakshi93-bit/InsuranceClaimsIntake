"""
main.py
FastAPI application entry point for the Insurance Claims Intake app.

Responsibilities:
- Load environment configuration (.env via python-dotenv)
- Initialise and seed the SQLite database on startup, close on shutdown
- Mount static files and Jinja2 templates
- Register API routers (claims, policies)
- Serve browser-facing HTML pages
- Catch all unhandled exceptions and return a generic 500 response
"""

import os
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db.database import init_db, set_db
from db.seed import seed
from routers import claims, policies

# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------
load_dotenv()
DB_PATH = os.getenv("DATABASE_PATH", "claims.db")

# ---------------------------------------------------------------------------
# Static files and templates directories
# ---------------------------------------------------------------------------
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)

TEMPLATES_DIR = Path(__file__).parent / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=TEMPLATES_DIR)


# ---------------------------------------------------------------------------
# Application lifespan — runs DB init/seed on startup and closes on shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = init_db(DB_PATH)
    seed(conn)
    set_db(conn)
    yield
    conn.close()


app = FastAPI(lifespan=lifespan)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(claims.router)
app.include_router(policies.router)

# Static files are served at /static (CSS, JS, images)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------------------------------------------------------------------------
# Page routes — browser-facing HTML pages (not API)
# ---------------------------------------------------------------------------
@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/intake")
def intake_page(request: Request):
    return templates.TemplateResponse(request=request, name="intake.html")


@app.get("/summary")
def summary_page(request: Request, id: str | None = None):
    return templates.TemplateResponse(
        request=request, name="summary.html", context={"claim_id": id}
    )


@app.get("/search")
def search_page(request: Request):
    return templates.TemplateResponse(request=request, name="search.html")


# ---------------------------------------------------------------------------
# Exception handler — never expose stack traces to the client
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()  # log to stderr only
    return JSONResponse(
        status_code=500, content={"error": "Internal server error"}
    )
