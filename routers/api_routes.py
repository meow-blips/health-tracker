import logging
import io
import csv
from fastapi import APIRouter, Request, Depends, Form, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from database import get_db
from models import (
    User, WaterLog, CalorieLog, ExerciseLog,
    Medication, MedicationLog, SleepLog, PeriodLog,
    Allergy, MoodLog, GoalSettings, WeightLog,
)
from routers.auth_routes import get_current_user
from config import get_settings
from datetime import date, datetime, timedelta
from nutrition_db import search_foods

logger = logging.getLogger("healthtrack.api")
router = APIRouter(prefix="/api")
settings = get_settings()


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def get_user_goals(user: User, db: Session) -> GoalSettings:
    goals = db.query(GoalSettings).filter(GoalSettings.user_id == user.user_id).first()
    if not goals:
        goals = GoalSettings(user_id=user.user_id)
        db.add(goals)
        db.commit()
        db.refresh(goals)
    return goals


# ═════════════════════════════════════════════════════════════════════════════
#  GOALS
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/goals")
async def get_goals(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    goals = get_user_goals(user, db)
    return JSONResponse({
        "water_ml": goals.water_ml,
        "calories": goals.calories,
        "exercise_min": goals.exercise_min,
        "sleep_hours": goals.sleep_hours,
    })


@router.post("/goals")
async def update_goals(
    request: Request,
    water_ml: int = Form(None),
    calories: int = Form(None),
    exercise_min: int = Form(None),
    sleep_hours: float = Form(None),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    goals = get_user_goals(user, db)
    if water_ml is not None:
        goals.water_ml = max(500, min(water_ml, settings.MAX_DAILY_WATER_ML))
    if calories is not None:
        goals.calories = max(500, min(calories, 10000))
    if exercise_min is not None:
        goals.exercise_min = max(5, min(exercise_min, 300))
    if sleep_hours is not None:
        goals.sleep_hours = max(1, min(sleep_hours, 16))
    db.commit()
    logger.info("Goals updated for user %s", user.username)
    return JSONResponse({
        "water_ml": goals.water_ml,
        "calories": goals.calories,
        "exercise_min": goals.exercise_min,
        "sleep_hours": goals.sleep_hours,
    })


# ═════════════════════════════════════════════════════════════════════════════
#  WATER LOG
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/water")
async def log_water(
    request: Request,
    ml: int = Form(250),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    ml = max(1, min(ml, 2000))
    today = date.today()
    cap = settings.MAX_DAILY_WATER_ML

    log = db.query(WaterLog).filter(
        WaterLog.user_id == user.user_id, WaterLog.date == today
    ).first()
    if log:
        new_total = min(log.ml_total + ml, cap)
        log.ml_total = new_total
        log.glasses = round(new_total / 250)
    else:
        capped = min(ml, cap)
        log = WaterLog(
            user_id=user.user_id, date=today,
            glasses=round(capped / 250), ml_total=capped,
        )
        db.add(log)
    db.commit()
    at_limit = log.ml_total >= cap
    return JSONResponse({
        "ml": log.ml_total,
        "liters": round(log.ml_total / 1000, 2),
        "at_limit": at_limit,
    })


@router.post("/water/set")
async def set_water(
    request: Request,
    ml: int = Form(0),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    cap = settings.MAX_DAILY_WATER_ML
    ml = max(0, min(ml, cap))
    today = date.today()

    log = db.query(WaterLog).filter(
        WaterLog.user_id == user.user_id, WaterLog.date == today
    ).first()
    if log:
        log.ml_total = ml
        log.glasses = round(ml / 250)
    else:
        log = WaterLog(
            user_id=user.user_id, date=today,
            glasses=round(ml / 250), ml_total=ml,
        )
        db.add(log)
    db.commit()
    return JSONResponse({
        "ml": log.ml_total,
        "liters": round(log.ml_total / 1000, 2),
    })


@router.get("/water/today")
async def get_water_today(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    log = db.query(WaterLog).filter(
        WaterLog.user_id == user.user_id, WaterLog.date == date.today()
    ).first()
    ml = log.ml_total if log else 0
    return JSONResponse({
        "ml": ml,
        "liters": round(ml / 1000, 2),
    })


@router.get("/water/history")
async def get_water_history(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    start = date.today() - timedelta(days=days - 1)
    logs = db.query(WaterLog).filter(
        WaterLog.user_id == user.user_id, WaterLog.date >= start
    ).order_by(WaterLog.date).all()
    return JSONResponse([
        {"date": l.date.isoformat(), "ml": l.ml_total, "liters": round(l.ml_total / 1000, 2)}
        for l in logs
    ])


# ═════════════════════════════════════════════════════════════════════════════
#  CALORIE LOG
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/calories")
async def log_calories(
    request: Request,
    meal_type: str = Form("snack"),
    description: str = Form(""),
    calories: float = Form(0),
    protein_g: float = Form(0),
    carbs_g: float = Form(0),
    fat_g: float = Form(0),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    log = CalorieLog(
        user_id=user.user_id, date=date.today(), meal_type=meal_type,
        description=description[:500], calories=max(0, calories),
        protein_g=max(0, protein_g), carbs_g=max(0, carbs_g), fat_g=max(0, fat_g),
    )
    db.add(log)
    db.commit()
    return JSONResponse({"id": log.id, "calories": log.calories})


@router.get("/calories/today")
async def get_calories_today(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    logs = db.query(CalorieLog).filter(
        CalorieLog.user_id == user.user_id, CalorieLog.date == date.today()
    ).all()
    total = sum(l.calories for l in logs)
    total_protein = sum(l.protein_g for l in logs)
    total_carbs = sum(l.carbs_g for l in logs)
    total_fat = sum(l.fat_g for l in logs)
    meals = [{
        "id": l.id, "meal": l.meal_type, "desc": l.description,
        "cal": l.calories, "protein": l.protein_g,
        "carbs": l.carbs_g, "fat": l.fat_g,
    } for l in logs]
    return JSONResponse({
        "total": total, "protein": total_protein,
        "carbs": total_carbs, "fat": total_fat,
        "meals": meals,
    })


@router.get("/calories/history")
async def get_calories_history(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    start = date.today() - timedelta(days=days - 1)
    logs = db.query(
        CalorieLog.date,
        sqlfunc.sum(CalorieLog.calories).label("total_cal"),
        sqlfunc.sum(CalorieLog.protein_g).label("total_protein"),
        sqlfunc.sum(CalorieLog.carbs_g).label("total_carbs"),
        sqlfunc.sum(CalorieLog.fat_g).label("total_fat"),
    ).filter(
        CalorieLog.user_id == user.user_id, CalorieLog.date >= start
    ).group_by(CalorieLog.date).order_by(CalorieLog.date).all()
    return JSONResponse([{
        "date": l.date.isoformat(),
        "calories": round(l.total_cal or 0, 1),
        "protein": round(l.total_protein or 0, 1),
        "carbs": round(l.total_carbs or 0, 1),
        "fat": round(l.total_fat or 0, 1),
    } for l in logs])


@router.delete("/calories/{log_id}")
async def delete_calorie(log_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    log = db.query(CalorieLog).filter(
        CalorieLog.id == log_id, CalorieLog.user_id == user.user_id
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(log)
    db.commit()
    return JSONResponse({"ok": True})


# ═════════════════════════════════════════════════════════════════════════════
#  EXERCISE LOG
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/exercise")
async def log_exercise(
    request: Request,
    exercise_type: str = Form(""),
    duration_min: float = Form(0),
    calories_burned: float = Form(0),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    log = ExerciseLog(
        user_id=user.user_id, date=date.today(),
        exercise_type=exercise_type[:100],
        duration_min=max(0, duration_min),
        calories_burned=max(0, calories_burned),
        notes=notes[:500],
    )
    db.add(log)
    db.commit()
    return JSONResponse({"id": log.id, "duration": log.duration_min, "burned": log.calories_burned})


@router.get("/exercise/today")
async def get_exercise_today(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    logs = db.query(ExerciseLog).filter(
        ExerciseLog.user_id == user.user_id, ExerciseLog.date == date.today()
    ).all()
    total_min = sum(l.duration_min for l in logs)
    total_burn = sum(l.calories_burned for l in logs)
    items = [{
        "id": l.id, "type": l.exercise_type,
        "min": l.duration_min, "burned": l.calories_burned,
        "notes": l.notes,
    } for l in logs]
    return JSONResponse({"total_min": total_min, "total_burned": total_burn, "items": items})


@router.get("/exercise/history")
async def get_exercise_history(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    start = date.today() - timedelta(days=days - 1)
    logs = db.query(
        ExerciseLog.date,
        sqlfunc.sum(ExerciseLog.duration_min).label("total_min"),
        sqlfunc.sum(ExerciseLog.calories_burned).label("total_burned"),
    ).filter(
        ExerciseLog.user_id == user.user_id, ExerciseLog.date >= start
    ).group_by(ExerciseLog.date).order_by(ExerciseLog.date).all()
    return JSONResponse([{
        "date": l.date.isoformat(),
        "duration_min": round(l.total_min or 0, 1),
        "calories_burned": round(l.total_burned or 0, 1),
    } for l in logs])


@router.delete("/exercise/{log_id}")
async def delete_exercise(log_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    log = db.query(ExerciseLog).filter(
        ExerciseLog.id == log_id, ExerciseLog.user_id == user.user_id
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(log)
    db.commit()
    return JSONResponse({"ok": True})


# ═════════════════════════════════════════════════════════════════════════════
#  MEDICATIONS
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/medications")
async def add_medication(
    request: Request,
    name: str = Form(...),
    dosage: str = Form(""),
    frequency: str = Form("daily"),
    time_of_day: str = Form("morning"),
    pills_remaining: int = Form(30),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    med = Medication(
        user_id=user.user_id, name=name[:200], dosage=dosage[:100],
        frequency=frequency, time_of_day=time_of_day,
        pills_remaining=max(0, pills_remaining),
    )
    db.add(med)
    db.commit()
    return JSONResponse({"id": med.id, "name": med.name})


@router.get("/medications")
async def get_medications(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    meds = db.query(Medication).filter(
        Medication.user_id == user.user_id, Medication.active == True
    ).all()

    today = date.today()
    result = []
    for m in meds:
        taken_today = db.query(MedicationLog).filter(
            MedicationLog.medication_id == m.id,
            MedicationLog.date == today,
            MedicationLog.taken == True,
        ).first()
        result.append({
            "id": m.id, "name": m.name, "dosage": m.dosage,
            "frequency": m.frequency, "time": m.time_of_day,
            "pills_remaining": m.pills_remaining,
            "needs_refill": m.pills_remaining <= m.notify_refill_at,
            "taken_today": taken_today is not None,
        })
    return JSONResponse(result)


@router.post("/medications/{med_id}/take")
async def take_medication(med_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    med = db.query(Medication).filter(
        Medication.id == med_id, Medication.user_id == user.user_id
    ).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")

    already = db.query(MedicationLog).filter(
        MedicationLog.medication_id == med_id,
        MedicationLog.date == date.today(),
        MedicationLog.taken == True,
    ).first()
    if already:
        return JSONResponse({
            "ok": False, "message": "Already taken today",
            "pills_remaining": med.pills_remaining,
            "needs_refill": med.pills_remaining <= med.notify_refill_at,
        })

    log = MedicationLog(
        user_id=user.user_id, medication_id=med_id,
        date=date.today(), taken=True, taken_at=datetime.utcnow(),
    )
    db.add(log)
    if med.pills_remaining > 0:
        med.pills_remaining -= 1
    db.commit()
    return JSONResponse({
        "ok": True, "pills_remaining": med.pills_remaining,
        "needs_refill": med.pills_remaining <= med.notify_refill_at,
    })


@router.put("/medications/{med_id}/refill")
async def refill_medication(
    med_id: int,
    request: Request,
    pills: int = Form(30),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    med = db.query(Medication).filter(
        Medication.id == med_id, Medication.user_id == user.user_id
    ).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    med.pills_remaining = max(0, pills)
    db.commit()
    return JSONResponse({"ok": True, "pills_remaining": med.pills_remaining})


@router.delete("/medications/{med_id}")
async def delete_medication(med_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    med = db.query(Medication).filter(
        Medication.id == med_id, Medication.user_id == user.user_id
    ).first()
    if med:
        med.active = False
        db.commit()
    return JSONResponse({"ok": True})


# ─── Medication Adherence ────────────────────────────────────────────────────

@router.get("/medications/adherence")
async def medication_adherence(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    start = date.today() - timedelta(days=days - 1)
    meds = db.query(Medication).filter(
        Medication.user_id == user.user_id, Medication.active == True
    ).all()

    result = []
    for med in meds:
        total_taken = db.query(sqlfunc.count(MedicationLog.id)).filter(
            MedicationLog.medication_id == med.id,
            MedicationLog.date >= start,
            MedicationLog.taken == True,
        ).scalar() or 0

        total_expected = days
        if med.frequency == "twice-daily":
            total_expected = days * 2
        elif med.frequency == "weekly":
            total_expected = max(1, days // 7)

        last_log = db.query(MedicationLog).filter(
            MedicationLog.medication_id == med.id,
            MedicationLog.taken == True,
        ).order_by(MedicationLog.date.desc()).first()

        adherence = round((total_taken / total_expected * 100) if total_expected > 0 else 0, 1)
        result.append({
            "medication_id": med.id,
            "name": med.name,
            "total_expected": total_expected,
            "total_taken": total_taken,
            "adherence_pct": min(adherence, 100),
            "last_taken": last_log.date.isoformat() if last_log else None,
        })
    return JSONResponse(result)


# ═════════════════════════════════════════════════════════════════════════════
#  SLEEP LOG
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/sleep")
async def log_sleep(
    request: Request,
    hours: float = Form(0),
    quality: int = Form(3),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    hours = max(0, min(hours, 24))
    quality = max(1, min(quality, 5))
    today = date.today()
    log = db.query(SleepLog).filter(
        SleepLog.user_id == user.user_id, SleepLog.date == today
    ).first()
    if log:
        log.hours = hours
        log.quality = quality
    else:
        log = SleepLog(user_id=user.user_id, date=today, hours=hours, quality=quality)
        db.add(log)
    db.commit()
    return JSONResponse({"hours": log.hours, "quality": log.quality})


@router.get("/sleep/history")
async def get_sleep_history(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    start = date.today() - timedelta(days=days - 1)
    logs = db.query(SleepLog).filter(
        SleepLog.user_id == user.user_id, SleepLog.date >= start
    ).order_by(SleepLog.date).all()
    return JSONResponse([{
        "date": l.date.isoformat(), "hours": l.hours, "quality": l.quality,
    } for l in logs])


# ═════════════════════════════════════════════════════════════════════════════
#  MOOD LOG
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/mood")
async def log_mood(
    request: Request,
    mood: int = Form(3),
    energy: int = Form(3),
    stress: int = Form(3),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    mood = max(1, min(mood, 5))
    energy = max(1, min(energy, 5))
    stress = max(1, min(stress, 5))
    today = date.today()
    log = db.query(MoodLog).filter(
        MoodLog.user_id == user.user_id, MoodLog.date == today
    ).first()
    if log:
        log.mood = mood
        log.energy = energy
        log.stress = stress
        log.notes = notes[:500]
    else:
        log = MoodLog(
            user_id=user.user_id, date=today,
            mood=mood, energy=energy, stress=stress, notes=notes[:500],
        )
        db.add(log)
    db.commit()
    return JSONResponse({"mood": log.mood, "energy": log.energy, "stress": log.stress})


@router.get("/mood/history")
async def get_mood_history(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    start = date.today() - timedelta(days=days - 1)
    logs = db.query(MoodLog).filter(
        MoodLog.user_id == user.user_id, MoodLog.date >= start
    ).order_by(MoodLog.date).all()
    return JSONResponse([{
        "date": l.date.isoformat(),
        "mood": l.mood, "energy": l.energy, "stress": l.stress,
        "notes": l.notes,
    } for l in logs])


# ═════════════════════════════════════════════════════════════════════════════
#  PERIOD TRACKER
# ═════════════════════════════════════════════════════════════════════════════

def _compute_phase(cycle_day: int) -> str:
    if cycle_day <= 5:
        return "menstrual"
    if cycle_day <= 13:
        return "follicular"
    if cycle_day <= 16:
        return "ovulatory"
    if cycle_day <= 28:
        return "luteal"
    return "follicular"


@router.post("/period")
async def log_period(
    request: Request,
    flow_intensity: str = Form("medium"),
    symptoms: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    today = date.today()

    last_period = db.query(PeriodLog).filter(
        PeriodLog.user_id == user.user_id,
        PeriodLog.flow_intensity.in_(["light", "medium", "heavy"]),
    ).order_by(PeriodLog.date.desc()).first()

    cycle_day = 1
    phase = "menstrual"
    if last_period and last_period.date != today:
        days_diff = (today - last_period.date).days
        cycle_day = days_diff + 1
        if cycle_day > 28:
            cycle_day = 1
        phase = _compute_phase(cycle_day)

    log = db.query(PeriodLog).filter(
        PeriodLog.user_id == user.user_id, PeriodLog.date == today
    ).first()
    if log:
        log.flow_intensity = flow_intensity
        log.symptoms = symptoms[:500]
        log.phase = phase
        log.cycle_day = cycle_day
        log.notes = notes[:500]
    else:
        log = PeriodLog(
            user_id=user.user_id, date=today, flow_intensity=flow_intensity,
            symptoms=symptoms[:500], phase=phase, cycle_day=cycle_day, notes=notes[:500],
        )
        db.add(log)
    db.commit()
    return JSONResponse({"phase": phase, "cycle_day": cycle_day})


@router.get("/period/phase")
async def get_period_phase(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    log = db.query(PeriodLog).filter(
        PeriodLog.user_id == user.user_id
    ).order_by(PeriodLog.date.desc()).first()
    if not log:
        return JSONResponse({"phase": None, "cycle_day": None, "next_period_date": None, "cycle_length": None})

    days_since = (date.today() - log.date).days
    cycle_day = (log.cycle_day or 1) + days_since
    if cycle_day > 28:
        cycle_day = (cycle_day % 28) or 1
    phase = _compute_phase(cycle_day)

    cycle_length = _estimate_cycle_length(user.user_id, db)
    next_period = _predict_next_period(user.user_id, db, cycle_length)

    return JSONResponse({
        "phase": phase,
        "cycle_day": cycle_day,
        "next_period_date": next_period.isoformat() if next_period else None,
        "cycle_length": cycle_length,
    })


@router.get("/period/history")
async def get_period_history(
    request: Request,
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    start = date.today() - timedelta(days=days - 1)
    logs = db.query(PeriodLog).filter(
        PeriodLog.user_id == user.user_id, PeriodLog.date >= start
    ).order_by(PeriodLog.date).all()
    return JSONResponse([{
        "date": l.date.isoformat(), "flow": l.flow_intensity,
        "symptoms": l.symptoms, "phase": l.phase,
        "cycle_day": l.cycle_day, "notes": l.notes,
    } for l in logs])


def _estimate_cycle_length(user_id: int, db: Session) -> int:
    """Estimate average cycle length from menstrual-phase start dates."""
    starts = db.query(PeriodLog.date).filter(
        PeriodLog.user_id == user_id,
        PeriodLog.cycle_day == 1,
    ).order_by(PeriodLog.date.desc()).limit(6).all()
    if len(starts) < 2:
        return 28
    dates = sorted([s[0] for s in starts])
    diffs = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
    valid = [d for d in diffs if 20 <= d <= 40]
    return round(sum(valid) / len(valid)) if valid else 28


def _predict_next_period(user_id: int, db: Session, cycle_length: int) -> date | None:
    last_start = db.query(PeriodLog.date).filter(
        PeriodLog.user_id == user_id,
        PeriodLog.cycle_day == 1,
    ).order_by(PeriodLog.date.desc()).first()
    if not last_start:
        return None
    return last_start[0] + timedelta(days=cycle_length)


# ═════════════════════════════════════════════════════════════════════════════
#  ALLERGIES / EMERGENCY CARD
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/allergies")
async def add_allergy(
    request: Request,
    allergen: str = Form(...),
    severity: str = Form("moderate"),
    reaction: str = Form(""),
    emergency_contact: str = Form(""),
    emergency_phone: str = Form(""),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    allergy = Allergy(
        user_id=user.user_id, allergen=allergen[:200], severity=severity,
        reaction=reaction[:500], emergency_contact=emergency_contact[:200],
        emergency_phone=emergency_phone[:50],
    )
    db.add(allergy)
    db.commit()
    return JSONResponse({"id": allergy.id, "allergen": allergy.allergen})


@router.get("/allergies")
async def get_allergies(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    allergies = db.query(Allergy).filter(Allergy.user_id == user.user_id).all()
    return JSONResponse([{
        "id": a.id, "allergen": a.allergen, "severity": a.severity,
        "reaction": a.reaction, "contact": a.emergency_contact,
        "phone": a.emergency_phone,
    } for a in allergies])


@router.delete("/allergies/{allergy_id}")
async def delete_allergy(allergy_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    allergy = db.query(Allergy).filter(
        Allergy.id == allergy_id, Allergy.user_id == user.user_id
    ).first()
    if not allergy:
        raise HTTPException(status_code=404, detail="Allergy not found")
    db.delete(allergy)
    db.commit()
    return JSONResponse({"ok": True})


# ═════════════════════════════════════════════════════════════════════════════
#  WEIGHT TRACKING
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/weight")
async def log_weight(
    request: Request,
    weight_kg: float = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    weight_kg = max(5, min(weight_kg, 500))
    today = date.today()

    bmi_val = None
    if user.height_cm and user.height_cm > 0:
        bmi_val = round(weight_kg / ((user.height_cm / 100) ** 2), 1)

    log = db.query(WeightLog).filter(
        WeightLog.user_id == user.user_id, WeightLog.date == today
    ).first()
    if log:
        log.weight_kg = weight_kg
        log.bmi = bmi_val
        log.notes = notes[:300]
    else:
        log = WeightLog(
            user_id=user.user_id, date=today,
            weight_kg=weight_kg, bmi=bmi_val, notes=notes[:300],
        )
        db.add(log)

    user.weight_kg = weight_kg
    db.commit()

    return JSONResponse({
        "id": log.id, "date": today.isoformat(),
        "weight_kg": log.weight_kg, "bmi": log.bmi,
    })


@router.get("/weight/history")
async def get_weight_history(
    request: Request,
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    start = date.today() - timedelta(days=days - 1)
    logs = db.query(WeightLog).filter(
        WeightLog.user_id == user.user_id, WeightLog.date >= start
    ).order_by(WeightLog.date).all()
    return JSONResponse([{
        "id": l.id, "date": l.date.isoformat(),
        "weight_kg": l.weight_kg, "bmi": l.bmi, "notes": l.notes,
    } for l in logs])


# ═════════════════════════════════════════════════════════════════════════════
#  NUTRITION SEARCH
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/nutrition/search")
async def nutrition_search(
    request: Request,
    q: str = Query("", min_length=0, max_length=200),
    db: Session = Depends(get_db),
):
    require_user(request, db)
    results = search_foods(q, limit=10)
    return JSONResponse(results)


# ═════════════════════════════════════════════════════════════════════════════
#  STREAKS
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/streaks")
async def get_streaks(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    today = date.today()
    start = today - timedelta(days=365)

    active_dates = set()
    for Model in [WaterLog, CalorieLog, ExerciseLog, SleepLog, MoodLog]:
        dates = db.query(Model.date).filter(
            Model.user_id == user.user_id, Model.date >= start
        ).distinct().all()
        active_dates.update(d[0] for d in dates)

    if not active_dates:
        return JSONResponse({
            "current_streak": 0, "longest_streak": 0,
            "total_active_days": 0, "total_days_tracked": 0,
        })

    current = 0
    d = today
    while d in active_dates:
        current += 1
        d -= timedelta(days=1)

    longest = 0
    streak = 0
    total_days = (today - start).days + 1
    for i in range(total_days):
        d = start + timedelta(days=i)
        if d in active_dates:
            streak += 1
            longest = max(longest, streak)
        else:
            streak = 0

    return JSONResponse({
        "current_streak": current,
        "longest_streak": longest,
        "total_active_days": len(active_dates),
        "total_days_tracked": total_days,
    })


# ═════════════════════════════════════════════════════════════════════════════
#  DASHBOARD SUMMARY / TRENDS / HEATMAP
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/dashboard/summary")
async def dashboard_summary(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    today = date.today()
    goals = get_user_goals(user, db)

    water = db.query(WaterLog).filter(
        WaterLog.user_id == user.user_id, WaterLog.date == today
    ).first()
    cal_logs = db.query(CalorieLog).filter(
        CalorieLog.user_id == user.user_id, CalorieLog.date == today
    ).all()
    ex_logs = db.query(ExerciseLog).filter(
        ExerciseLog.user_id == user.user_id, ExerciseLog.date == today
    ).all()
    sleep = db.query(SleepLog).filter(
        SleepLog.user_id == user.user_id, SleepLog.date == today
    ).first()
    mood = db.query(MoodLog).filter(
        MoodLog.user_id == user.user_id, MoodLog.date == today
    ).first()

    return JSONResponse({
        "water_ml": water.ml_total if water else 0,
        "water_goal_ml": goals.water_ml,
        "calories_total": sum(l.calories for l in cal_logs),
        "calories_goal": goals.calories,
        "protein_total": sum(l.protein_g for l in cal_logs),
        "carbs_total": sum(l.carbs_g for l in cal_logs),
        "fat_total": sum(l.fat_g for l in cal_logs),
        "exercise_min": sum(l.duration_min for l in ex_logs),
        "exercise_goal": goals.exercise_min,
        "exercise_burned": sum(l.calories_burned for l in ex_logs),
        "sleep_hours": sleep.hours if sleep else 0,
        "sleep_quality": sleep.quality if sleep else 0,
        "sleep_goal": goals.sleep_hours,
        "mood": mood.mood if mood else 0,
        "energy": mood.energy if mood else 0,
        "stress": mood.stress if mood else 0,
        "bmi": user.bmi,
        "bmi_category": user.bmi_category,
    })


@router.get("/dashboard/trends")
async def dashboard_trends(
    request: Request,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    today = date.today()
    result = []

    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        water = db.query(WaterLog).filter(
            WaterLog.user_id == user.user_id, WaterLog.date == d
        ).first()
        cals = db.query(CalorieLog).filter(
            CalorieLog.user_id == user.user_id, CalorieLog.date == d
        ).all()
        exer = db.query(ExerciseLog).filter(
            ExerciseLog.user_id == user.user_id, ExerciseLog.date == d
        ).all()
        sleep = db.query(SleepLog).filter(
            SleepLog.user_id == user.user_id, SleepLog.date == d
        ).first()
        mood = db.query(MoodLog).filter(
            MoodLog.user_id == user.user_id, MoodLog.date == d
        ).first()

        result.append({
            "date": d.isoformat(),
            "label": d.strftime("%a"),
            "water_ml": water.ml_total if water else 0,
            "calories": sum(c.calories for c in cals),
            "exercise": sum(e.duration_min for e in exer),
            "exercise_burned": sum(e.calories_burned for e in exer),
            "sleep": sleep.hours if sleep else 0,
            "sleep_quality": sleep.quality if sleep else 0,
            "mood": mood.mood if mood else 0,
        })

    return JSONResponse(result)


@router.get("/dashboard/heatmap")
async def dashboard_heatmap(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    today = date.today()
    start = today - timedelta(days=90)
    result = {}

    water_logs = db.query(WaterLog.date, WaterLog.ml_total).filter(
        WaterLog.user_id == user.user_id, WaterLog.date >= start
    ).all()
    cal_dates = {d[0] for d in db.query(CalorieLog.date).filter(
        CalorieLog.user_id == user.user_id, CalorieLog.date >= start
    ).distinct().all()}
    ex_dates = {d[0] for d in db.query(ExerciseLog.date).filter(
        ExerciseLog.user_id == user.user_id, ExerciseLog.date >= start
    ).distinct().all()}
    sleep_dates = {d[0] for d in db.query(SleepLog.date).filter(
        SleepLog.user_id == user.user_id, SleepLog.date >= start
    ).distinct().all()}
    mood_dates = {d[0] for d in db.query(MoodLog.date).filter(
        MoodLog.user_id == user.user_id, MoodLog.date >= start
    ).distinct().all()}
    water_map = {w.date: w.ml_total for w in water_logs}

    for i in range(91):
        d = start + timedelta(days=i)
        score = 0
        if d in water_map and water_map[d] >= 1000:
            score += 1
        if d in cal_dates:
            score += 1
        if d in ex_dates:
            score += 1
        if d in sleep_dates:
            score += 1
        if d in mood_dates:
            score += 1
        result[d.isoformat()] = score

    return JSONResponse(result)


# ═════════════════════════════════════════════════════════════════════════════
#  DATA EXPORT (CSV)
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/export/csv")
async def export_csv(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    today = date.today()
    start = today - timedelta(days=days - 1)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Date", "Water (ml)", "Calories", "Protein (g)", "Carbs (g)", "Fat (g)",
        "Exercise (min)", "Calories Burned", "Sleep (hrs)", "Sleep Quality",
        "Mood", "Energy", "Stress",
    ])

    for i in range(days):
        d = start + timedelta(days=i)
        water = db.query(WaterLog).filter(
            WaterLog.user_id == user.user_id, WaterLog.date == d
        ).first()
        cals = db.query(CalorieLog).filter(
            CalorieLog.user_id == user.user_id, CalorieLog.date == d
        ).all()
        exer = db.query(ExerciseLog).filter(
            ExerciseLog.user_id == user.user_id, ExerciseLog.date == d
        ).all()
        sleep = db.query(SleepLog).filter(
            SleepLog.user_id == user.user_id, SleepLog.date == d
        ).first()
        mood = db.query(MoodLog).filter(
            MoodLog.user_id == user.user_id, MoodLog.date == d
        ).first()

        writer.writerow([
            d.isoformat(),
            water.ml_total if water else 0,
            round(sum(c.calories for c in cals), 1),
            round(sum(c.protein_g for c in cals), 1),
            round(sum(c.carbs_g for c in cals), 1),
            round(sum(c.fat_g for c in cals), 1),
            round(sum(e.duration_min for e in exer), 1),
            round(sum(e.calories_burned for e in exer), 1),
            sleep.hours if sleep else 0,
            sleep.quality if sleep else "",
            mood.mood if mood else "",
            mood.energy if mood else "",
            mood.stress if mood else "",
        ])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=healthtrack_export_{today}.csv"},
    )


@router.get("/export/json")
async def export_json(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    today = date.today()
    start = today - timedelta(days=days - 1)

    data = {
        "user": user.username,
        "exported_at": datetime.utcnow().isoformat(),
        "range": {"from": start.isoformat(), "to": today.isoformat()},
        "days": [],
    }

    for i in range(days):
        d = start + timedelta(days=i)
        water = db.query(WaterLog).filter(
            WaterLog.user_id == user.user_id, WaterLog.date == d
        ).first()
        cals = db.query(CalorieLog).filter(
            CalorieLog.user_id == user.user_id, CalorieLog.date == d
        ).all()
        exer = db.query(ExerciseLog).filter(
            ExerciseLog.user_id == user.user_id, ExerciseLog.date == d
        ).all()
        sleep = db.query(SleepLog).filter(
            SleepLog.user_id == user.user_id, SleepLog.date == d
        ).first()
        mood = db.query(MoodLog).filter(
            MoodLog.user_id == user.user_id, MoodLog.date == d
        ).first()

        data["days"].append({
            "date": d.isoformat(),
            "water_ml": water.ml_total if water else 0,
            "calories": round(sum(c.calories for c in cals), 1),
            "protein_g": round(sum(c.protein_g for c in cals), 1),
            "carbs_g": round(sum(c.carbs_g for c in cals), 1),
            "fat_g": round(sum(c.fat_g for c in cals), 1),
            "exercise_min": round(sum(e.duration_min for e in exer), 1),
            "calories_burned": round(sum(e.calories_burned for e in exer), 1),
            "sleep_hours": sleep.hours if sleep else 0,
            "sleep_quality": sleep.quality if sleep else None,
            "mood": mood.mood if mood else None,
            "energy": mood.energy if mood else None,
            "stress": mood.stress if mood else None,
        })

    return JSONResponse(data)


# ═════════════════════════════════════════════════════════════════════════════
#  PDF REPORT
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/report/pdf")
async def generate_report(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    today = date.today()
    week_start = today - timedelta(days=6)
    goals = get_user_goals(user, db)

    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("HealthTrack Weekly Report", styles["Title"]))
    elements.append(Paragraph(f"User: {user.full_name or user.username}", styles["Normal"]))
    elements.append(Paragraph(f"Period: {week_start} to {today}", styles["Normal"]))
    elements.append(Paragraph(
        f"Goals: Water {goals.water_ml}ml | Cal {goals.calories} | "
        f"Exercise {goals.exercise_min}min | Sleep {goals.sleep_hours}hr",
        styles["Normal"],
    ))
    elements.append(Spacer(1, 20))

    if user.bmi:
        elements.append(Paragraph(f"BMI: {user.bmi} ({user.bmi_category})", styles["Heading2"]))
        elements.append(Spacer(1, 10))

    data = [["Date", "Water", "Calories", "Exercise", "Sleep", "Mood"]]
    for i in range(7):
        d = week_start + timedelta(days=i)
        water = db.query(WaterLog).filter(WaterLog.user_id == user.user_id, WaterLog.date == d).first()
        cals = db.query(CalorieLog).filter(CalorieLog.user_id == user.user_id, CalorieLog.date == d).all()
        exer = db.query(ExerciseLog).filter(ExerciseLog.user_id == user.user_id, ExerciseLog.date == d).all()
        sleep = db.query(SleepLog).filter(SleepLog.user_id == user.user_id, SleepLog.date == d).first()
        mood = db.query(MoodLog).filter(MoodLog.user_id == user.user_id, MoodLog.date == d).first()
        w_ml = water.ml_total if water else 0
        data.append([
            d.strftime("%b %d"),
            f"{round(w_ml/1000, 1)}L",
            f"{int(sum(c.calories for c in cals))} cal",
            f"{int(sum(e.duration_min for e in exer))} min",
            f"{sleep.hours if sleep else 0} hr",
            f"{mood.mood if mood else '-'}/5",
        ])

    table = Table(data, colWidths=[70, 60, 70, 70, 60, 50])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c5cfc")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    allergies = db.query(Allergy).filter(Allergy.user_id == user.user_id).all()
    if allergies:
        elements.append(Paragraph("Allergies & Emergency Information", styles["Heading2"]))
        for a in allergies:
            text = f"• {a.allergen} (Severity: {a.severity})"
            if a.reaction:
                text += f" — {a.reaction}"
            elements.append(Paragraph(text, styles["Normal"]))
            if a.emergency_contact:
                elements.append(Paragraph(
                    f"  Emergency Contact: {a.emergency_contact} — {a.emergency_phone}",
                    styles["Normal"],
                ))
        elements.append(Spacer(1, 10))

    meds = db.query(Medication).filter(
        Medication.user_id == user.user_id, Medication.active == True
    ).all()
    if meds:
        elements.append(Paragraph("Active Medications", styles["Heading2"]))
        for m in meds:
            elements.append(Paragraph(
                f"• {m.name} ({m.dosage}) — {m.frequency}, {m.time_of_day} — {m.pills_remaining} pills left",
                styles["Normal"],
            ))

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=healthtrack_report_{today}.pdf"},
    )
