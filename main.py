from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import User
from routers.auth_routes import router as auth_router, get_current_user
from routers.api_routes import router as api_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="HealthTrack", description="Your Health, Simplified")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth_router)
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    user = None
    token = request.cookies.get("access_token")
    if token:
        from auth import decode_access_token
        payload = decode_access_token(token)
        if payload:
            db = next(get_db())
            user = db.query(User).filter(User.user_id == payload.get("user_id")).first()
    return templates.TemplateResponse("landing.html", {"request": request, "user": user})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return HTMLResponse(
            '<script>window.location.href="/login";</script>', status_code=200
        )
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})
