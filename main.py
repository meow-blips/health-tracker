import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import get_settings
from database import engine, Base, get_db
from models import User
from middleware import register_middleware, setup_logging
from routers.auth_routes import router as auth_router, get_current_user
from routers.api_routes import router as api_router

settings = get_settings()
logger = logging.getLogger("healthtrack")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Your Health, Simplified — Track 11 health metrics in one dashboard.",
    lifespan=lifespan,
)

register_middleware(app)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth_router)
app.include_router(api_router)


# ─── Health Check ────────────────────────────────────────────────────────────

@app.get("/health", response_class=JSONResponse)
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    })


# ─── Landing Page ────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    user = None
    token = request.cookies.get("access_token")
    if token:
        from auth import decode_access_token
        payload = decode_access_token(token)
        if payload:
            db = next(get_db())
            try:
                user = db.query(User).filter(User.user_id == payload.get("user_id")).first()
            finally:
                db.close()
    return templates.TemplateResponse("landing.html", {"request": request, "user": user})


# ─── Dashboard ───────────────────────────────────────────────────────────────

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return HTMLResponse(
            '<script>window.location.href="/login";</script>', status_code=200,
        )
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})
