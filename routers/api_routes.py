from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from database import get_db
from models import (
    User, WaterLog, CalorieLog, ExerciseLog,
    Medication, MedicationLog, SleepLog, PeriodLog, Allergy, MoodLog,
)
from routers.auth_routes import get_current_user
from datetime import date, datetime, timedelta
import json
import io

router = APIRouter(prefix="/api")


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# ─── Water Log ───────────────────────────────────────────────────────────────

@router.post("/water")
async def log_water(
    request: Request,
    glasses: int = Form(1),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    today = date.today()
    log = db.query(WaterLog).filter(WaterLog.user_id == user.user_id, WaterLog.date == today).first()
    if log:
        log.glasses += glasses
        log.ml_total = log.glasses * 250
    else:
        log = WaterLog(user_id=user.user_id, date=today, glasses=glasses, ml_total=glasses * 250)
        db.add(log)
    db.commit()
    return JSONResponse({"glasses": log.glasses, "ml": log.ml_total})


@router.get("/water/today")
async def get_water_today(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    log = db.query(WaterLog).filter(WaterLog.user_id == user.user_id, WaterLog.date == date.today()).first()
    return JSONResponse({"glasses": log.glasses if log else 0, "ml": log.ml_total if log else 0})


# ─── Calorie Log ─────────────────────────────────────────────────────────────

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
        description=description, calories=calories,
        protein_g=protein_g, carbs_g=carbs_g, fat_g=fat_g,
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
    meals = [{"id": l.id, "meal": l.meal_type, "desc": l.description, "cal": l.calories} for l in logs]
    return JSONResponse({"total": total, "meals": meals})


@router.delete("/calories/{log_id}")
async def delete_calorie(log_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    log = db.query(CalorieLog).filter(CalorieLog.id == log_id, CalorieLog.user_id == user.user_id).first()
    if log:
        db.delete(log)
        db.commit()
    return JSONResponse({"ok": True})


# ─── Exercise Log ────────────────────────────────────────────────────────────

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
        user_id=user.user_id, date=date.today(), exercise_type=exercise_type,
        duration_min=duration_min, calories_burned=calories_burned, notes=notes,
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
    items = [{"id": l.id, "type": l.exercise_type, "min": l.duration_min, "burned": l.calories_burned} for l in logs]
    return JSONResponse({"total_min": total_min, "total_burned": total_burn, "items": items})


# ─── Medications ─────────────────────────────────────────────────────────────

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
        user_id=user.user_id, name=name, dosage=dosage,
        frequency=frequency, time_of_day=time_of_day, pills_remaining=pills_remaining,
    )
    db.add(med)
    db.commit()
    return JSONResponse({"id": med.id, "name": med.name})


@router.get("/medications")
async def get_medications(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    meds = db.query(Medication).filter(Medication.user_id == user.user_id, Medication.active == True).all()
    return JSONResponse([{
        "id": m.id, "name": m.name, "dosage": m.dosage,
        "frequency": m.frequency, "time": m.time_of_day,
        "pills_remaining": m.pills_remaining,
        "needs_refill": m.pills_remaining <= m.notify_refill_at,
    } for m in meds])


@router.post("/medications/{med_id}/take")
async def take_medication(med_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    med = db.query(Medication).filter(Medication.id == med_id, Medication.user_id == user.user_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")

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


@router.delete("/medications/{med_id}")
async def delete_medication(med_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    med = db.query(Medication).filter(Medication.id == med_id, Medication.user_id == user.user_id).first()
    if med:
        med.active = False
        db.commit()
    return JSONResponse({"ok": True})


# ─── Sleep Log ───────────────────────────────────────────────────────────────

@router.post("/sleep")
async def log_sleep(
    request: Request,
    hours: float = Form(0),
    quality: int = Form(3),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    today = date.today()
    log = db.query(SleepLog).filter(SleepLog.user_id == user.user_id, SleepLog.date == today).first()
    if log:
        log.hours = hours
        log.quality = quality
    else:
        log = SleepLog(user_id=user.user_id, date=today, hours=hours, quality=quality)
        db.add(log)
    db.commit()
    return JSONResponse({"hours": log.hours, "quality": log.quality})


# ─── Mood Log ────────────────────────────────────────────────────────────────

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
    today = date.today()
    log = db.query(MoodLog).filter(MoodLog.user_id == user.user_id, MoodLog.date == today).first()
    if log:
        log.mood = mood
        log.energy = energy
        log.stress = stress
        log.notes = notes
    else:
        log = MoodLog(user_id=user.user_id, date=today, mood=mood, energy=energy, stress=stress, notes=notes)
        db.add(log)
    db.commit()
    return JSONResponse({"mood": log.mood, "energy": log.energy, "stress": log.stress})


# ─── Period Tracker ──────────────────────────────────────────────────────────

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
        if cycle_day <= 5:
            phase = "menstrual"
        elif cycle_day <= 13:
            phase = "follicular"
        elif cycle_day <= 16:
            phase = "ovulatory"
        elif cycle_day <= 28:
            phase = "luteal"
        else:
            cycle_day = 1
            phase = "menstrual"

    log = db.query(PeriodLog).filter(PeriodLog.user_id == user.user_id, PeriodLog.date == today).first()
    if log:
        log.flow_intensity = flow_intensity
        log.symptoms = symptoms
        log.phase = phase
        log.cycle_day = cycle_day
        log.notes = notes
    else:
        log = PeriodLog(
            user_id=user.user_id, date=today, flow_intensity=flow_intensity,
            symptoms=symptoms, phase=phase, cycle_day=cycle_day, notes=notes,
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
        return JSONResponse({"phase": None, "cycle_day": None})

    days_since = (date.today() - log.date).days
    cycle_day = (log.cycle_day or 1) + days_since
    if cycle_day <= 5:
        phase = "menstrual"
    elif cycle_day <= 13:
        phase = "follicular"
    elif cycle_day <= 16:
        phase = "ovulatory"
    elif cycle_day <= 28:
        phase = "luteal"
    else:
        phase = "follicular"
        cycle_day = cycle_day % 28 or 1
    return JSONResponse({"phase": phase, "cycle_day": cycle_day})


# ─── Allergies / Emergency Card ──────────────────────────────────────────────

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
        user_id=user.user_id, allergen=allergen, severity=severity,
        reaction=reaction, emergency_contact=emergency_contact, emergency_phone=emergency_phone,
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
        "reaction": a.reaction, "contact": a.emergency_contact, "phone": a.emergency_phone,
    } for a in allergies])


@router.delete("/allergies/{allergy_id}")
async def delete_allergy(allergy_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    allergy = db.query(Allergy).filter(Allergy.id == allergy_id, Allergy.user_id == user.user_id).first()
    if allergy:
        db.delete(allergy)
        db.commit()
    return JSONResponse({"ok": True})


# ─── Dashboard Data (7-day trends) ──────────────────────────────────────────

@router.get("/dashboard/summary")
async def dashboard_summary(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    today = date.today()

    water = db.query(WaterLog).filter(WaterLog.user_id == user.user_id, WaterLog.date == today).first()
    cal_logs = db.query(CalorieLog).filter(CalorieLog.user_id == user.user_id, CalorieLog.date == today).all()
    ex_logs = db.query(ExerciseLog).filter(ExerciseLog.user_id == user.user_id, ExerciseLog.date == today).all()
    sleep = db.query(SleepLog).filter(SleepLog.user_id == user.user_id, SleepLog.date == today).first()
    mood = db.query(MoodLog).filter(MoodLog.user_id == user.user_id, MoodLog.date == today).first()

    return JSONResponse({
        "water_glasses": water.glasses if water else 0,
        "water_goal": 8,
        "calories_total": sum(l.calories for l in cal_logs),
        "calories_goal": 2000,
        "exercise_min": sum(l.duration_min for l in ex_logs),
        "exercise_goal": 30,
        "exercise_burned": sum(l.calories_burned for l in ex_logs),
        "sleep_hours": sleep.hours if sleep else 0,
        "sleep_goal": 8,
        "mood": mood.mood if mood else 0,
        "energy": mood.energy if mood else 0,
        "bmi": user.bmi,
        "bmi_category": user.bmi_category,
    })


@router.get("/dashboard/trends")
async def dashboard_trends(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    today = date.today()
    days = []

    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        water = db.query(WaterLog).filter(WaterLog.user_id == user.user_id, WaterLog.date == d).first()
        cals = db.query(CalorieLog).filter(CalorieLog.user_id == user.user_id, CalorieLog.date == d).all()
        exer = db.query(ExerciseLog).filter(ExerciseLog.user_id == user.user_id, ExerciseLog.date == d).all()
        sleep = db.query(SleepLog).filter(SleepLog.user_id == user.user_id, SleepLog.date == d).first()

        days.append({
            "date": d.isoformat(),
            "label": d.strftime("%a"),
            "water": water.glasses if water else 0,
            "calories": sum(c.calories for c in cals),
            "exercise": sum(e.duration_min for e in exer),
            "exercise_burned": sum(e.calories_burned for e in exer),
            "sleep": sleep.hours if sleep else 0,
        })

    return JSONResponse(days)


@router.get("/dashboard/heatmap")
async def dashboard_heatmap(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    today = date.today()
    start = today - timedelta(days=90)
    result = {}

    water_logs = db.query(WaterLog.date, WaterLog.glasses).filter(
        WaterLog.user_id == user.user_id, WaterLog.date >= start
    ).all()
    cal_dates = db.query(CalorieLog.date).filter(
        CalorieLog.user_id == user.user_id, CalorieLog.date >= start
    ).distinct().all()
    ex_dates = db.query(ExerciseLog.date).filter(
        ExerciseLog.user_id == user.user_id, ExerciseLog.date >= start
    ).distinct().all()
    sleep_dates = db.query(SleepLog.date).filter(
        SleepLog.user_id == user.user_id, SleepLog.date >= start
    ).distinct().all()
    mood_dates = db.query(MoodLog.date).filter(
        MoodLog.user_id == user.user_id, MoodLog.date >= start
    ).distinct().all()

    cal_set = {d[0] for d in cal_dates}
    ex_set = {d[0] for d in ex_dates}
    sleep_set = {d[0] for d in sleep_dates}
    mood_set = {d[0] for d in mood_dates}
    water_map = {w.date: w.glasses for w in water_logs}

    for i in range(91):
        d = start + timedelta(days=i)
        score = 0
        if d in water_map and water_map[d] >= 4:
            score += 1
        if d in cal_set:
            score += 1
        if d in ex_set:
            score += 1
        if d in sleep_set:
            score += 1
        if d in mood_set:
            score += 1
        result[d.isoformat()] = score

    return JSONResponse(result)


# ─── PDF Report ──────────────────────────────────────────────────────────────

@router.get("/report/pdf")
async def generate_report(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    today = date.today()
    week_start = today - timedelta(days=6)

    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"HealthTrack Weekly Report", styles["Title"]))
    elements.append(Paragraph(f"User: {user.full_name or user.username}", styles["Normal"]))
    elements.append(Paragraph(f"Period: {week_start} to {today}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    if user.bmi:
        elements.append(Paragraph(f"BMI: {user.bmi} ({user.bmi_category})", styles["Heading2"]))
        elements.append(Spacer(1, 10))

    data = [["Date", "Water (glasses)", "Calories", "Exercise (min)", "Sleep (hrs)"]]
    for i in range(7):
        d = week_start + timedelta(days=i)
        water = db.query(WaterLog).filter(WaterLog.user_id == user.user_id, WaterLog.date == d).first()
        cals = db.query(CalorieLog).filter(CalorieLog.user_id == user.user_id, CalorieLog.date == d).all()
        exer = db.query(ExerciseLog).filter(ExerciseLog.user_id == user.user_id, ExerciseLog.date == d).all()
        sleep = db.query(SleepLog).filter(SleepLog.user_id == user.user_id, SleepLog.date == d).first()
        data.append([
            d.strftime("%b %d"),
            str(water.glasses if water else 0),
            str(int(sum(c.calories for c in cals))),
            str(int(sum(e.duration_min for e in exer))),
            str(sleep.hours if sleep else 0),
        ])

    table = Table(data, colWidths=[80, 100, 80, 100, 80])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
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
            elements.append(Paragraph(
                f"• {a.allergen} (Severity: {a.severity}) — {a.reaction}", styles["Normal"]
            ))
            if a.emergency_contact:
                elements.append(Paragraph(
                    f"  Emergency Contact: {a.emergency_contact} — {a.emergency_phone}", styles["Normal"]
                ))
        elements.append(Spacer(1, 10))

    meds = db.query(Medication).filter(Medication.user_id == user.user_id, Medication.active == True).all()
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
