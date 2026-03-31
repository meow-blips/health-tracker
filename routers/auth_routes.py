import logging
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import (
    hash_password, verify_password, create_access_token,
    decode_access_token, generate_reset_token, verify_reset_token,
)
from config import get_settings

logger = logging.getLogger("healthtrack.auth")
router = APIRouter()
templates = Jinja2Templates(directory="templates")
settings = get_settings()


# ─── Dependency: extract user from JWT cookie ────────────────────────────────

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    user = db.query(User).filter(User.user_id == payload.get("user_id")).first()
    return user


def require_auth(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


# ─── Login ───────────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    token = request.cookies.get("access_token")
    if token and decode_access_token(token):
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "user": None})


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    remember: bool = Form(False),
    db: Session = Depends(get_db),
):
    email = email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        logger.warning("Failed login attempt for %s", email)
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password.", "user": None},
            status_code=400,
        )

    logger.info("User %s logged in", user.username)
    token = create_access_token({"user_id": user.user_id, "email": user.email})
    response = RedirectResponse(url="/dashboard", status_code=303)
    max_age = 60 * 60 * 24 * 30 if remember else 60 * 60 * 24
    response.set_cookie(
        "access_token", token, max_age=max_age,
        httponly=True, samesite="lax",
    )
    return response


# ─── Registration ────────────────────────────────────────────────────────────

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
    email = email.lower().strip()
    username = username.strip()

    if len(password) < settings.MIN_PASSWORD_LENGTH:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": f"Password must be at least {settings.MIN_PASSWORD_LENGTH} characters.", "user": None},
            status_code=400,
        )

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

    logger.info("New user registered: %s (%s)", user.username, user.email)
    token = create_access_token({"user_id": user.user_id, "email": user.email})
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        "access_token", token,
        max_age=60 * 60 * 24 * settings.ACCESS_TOKEN_EXPIRE_DAYS,
        httponly=True, samesite="lax",
    )
    return response


# ─── Forgot / Reset Password ────────────────────────────────────────────────

@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request, "user": None})


@router.post("/forgot-password")
async def forgot_password(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    email = email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if user:
        token = generate_reset_token(email)
        logger.info("Password reset requested for %s", email)
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
        logger.info("Password reset completed for %s", email)
    return RedirectResponse(url="/login?reset=success", status_code=303)


# ─── Logout ──────────────────────────────────────────────────────────────────

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response


# ─── Password Change (authenticated) ────────────────────────────────────────

@router.post("/api/password/change")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not verify_password(current_password, user.password_hash):
        return JSONResponse(
            status_code=400,
            content={"detail": "Current password is incorrect."},
        )

    if len(new_password) < settings.MIN_PASSWORD_LENGTH:
        return JSONResponse(
            status_code=400,
            content={"detail": f"New password must be at least {settings.MIN_PASSWORD_LENGTH} characters."},
        )

    user.password_hash = hash_password(new_password)
    db.commit()
    logger.info("Password changed for user %s", user.username)
    return JSONResponse({"ok": True, "message": "Password updated successfully."})


# ─── Profile Update ──────────────────────────────────────────────────────────

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

    logger.info("Profile updated for user %s", user.username)
    return RedirectResponse(url="/dashboard?tab=profile&updated=1", status_code=303)


# ─── Account Deletion ────────────────────────────────────────────────────────

@router.post("/api/account/delete")
async def delete_account(
    request: Request,
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not verify_password(password, user.password_hash):
        return JSONResponse(
            status_code=400,
            content={"detail": "Password is incorrect. Account not deleted."},
        )

    logger.warning("Account deletion for user %s (%s)", user.username, user.email)
    db.delete(user)
    db.commit()

    response = JSONResponse({"ok": True, "message": "Account deleted."})
    response.delete_cookie("access_token")
    return response


# ─── Current User Info (JSON API) ────────────────────────────────────────────

@router.get("/api/me")
async def get_me(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return JSONResponse({
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "height_cm": user.height_cm,
        "weight_kg": user.weight_kg,
        "age": user.age,
        "gender": user.gender,
        "bmi": user.bmi,
        "bmi_category": user.bmi_category,
        "notify_meds": user.notify_meds,
        "notify_periods": user.notify_periods,
        "notify_water": user.notify_water,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    })
