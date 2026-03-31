from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import (
    hash_password, verify_password, create_access_token,
    decode_access_token, generate_reset_token, verify_reset_token,
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    user = db.query(User).filter(User.user_id == payload.get("user_id")).first()
    return user


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = None
    token = request.cookies.get("access_token")
    if token:
        payload = decode_access_token(token)
        if payload:
            return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "user": user})


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    remember: bool = Form(False),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password.", "user": None},
            status_code=400,
        )

    token = create_access_token({"user_id": user.user_id, "email": user.email})
    response = RedirectResponse(url="/dashboard", status_code=303)
    max_age = 60 * 60 * 24 * 30 if remember else 60 * 60 * 24
    response.set_cookie("access_token", token, max_age=max_age, httponly=True, samesite="lax")
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "user": None})


@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(""),
    height_cm: float = Form(None),
    weight_kg: float = Form(None),
    age: int = Form(None),
    gender: str = Form(None),
    notify_meds: bool = Form(True),
    notify_periods: bool = Form(True),
    notify_water: bool = Form(True),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Email already registered.", "user": None},
            status_code=400,
        )
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username already taken.", "user": None},
            status_code=400,
        )

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        height_cm=height_cm,
        weight_kg=weight_kg,
        age=age,
        gender=gender,
        notify_meds=notify_meds,
        notify_periods=notify_periods,
        notify_water=notify_water,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"user_id": user.user_id, "email": user.email})
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie("access_token", token, max_age=60 * 60 * 24 * 7, httponly=True, samesite="lax")
    return response


@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request, "user": None})


@router.post("/forgot-password")
async def forgot_password(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if user:
        token = generate_reset_token(email)
        return templates.TemplateResponse(
            "forgot_password.html",
            {
                "request": request,
                "success": True,
                "reset_link": f"/reset-password?token={token}",
                "user": None,
            },
        )
    return templates.TemplateResponse(
        "forgot_password.html",
        {"request": request, "error": "No account found with that email.", "user": None},
        status_code=400,
    )


@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str):
    email = verify_reset_token(token)
    if not email:
        return templates.TemplateResponse(
            "forgot_password.html",
            {"request": request, "error": "Invalid or expired reset link.", "user": None},
        )
    return templates.TemplateResponse(
        "reset_password.html", {"request": request, "token": token, "user": None}
    )


@router.post("/reset-password")
async def reset_password(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    email = verify_reset_token(token)
    if not email:
        return templates.TemplateResponse(
            "forgot_password.html",
            {"request": request, "error": "Invalid or expired reset link.", "user": None},
        )
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.password_hash = hash_password(password)
        db.commit()
    return RedirectResponse(url="/login?reset=success", status_code=303)


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response


@router.post("/profile/update")
async def update_profile(
    request: Request,
    full_name: str = Form(""),
    height_cm: float = Form(None),
    weight_kg: float = Form(None),
    age: int = Form(None),
    gender: str = Form(None),
    notify_meds: bool = Form(False),
    notify_periods: bool = Form(False),
    notify_water: bool = Form(False),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    user.full_name = full_name
    user.height_cm = height_cm
    user.weight_kg = weight_kg
    user.age = age
    user.gender = gender
    user.notify_meds = notify_meds
    user.notify_periods = notify_periods
    user.notify_water = notify_water
    db.commit()

    return RedirectResponse(url="/dashboard?tab=profile&updated=1", status_code=303)
