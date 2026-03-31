from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import date as DateType
from typing import Optional
import re


# ─── Auth Schemas ────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field("", max_length=200)
    height_cm: Optional[float] = Field(None, ge=30, le=300)
    weight_kg: Optional[float] = Field(None, ge=5, le=500)
    age: Optional[int] = Field(None, ge=1, le=150)
    gender: Optional[str] = Field(None, pattern=r"^(male|female|other)$")
    notify_meds: bool = True
    notify_periods: bool = True
    notify_water: bool = True

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str
    remember: bool = False


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field("", max_length=200)
    height_cm: Optional[float] = Field(None, ge=30, le=300)
    weight_kg: Optional[float] = Field(None, ge=5, le=500)
    age: Optional[int] = Field(None, ge=1, le=150)
    gender: Optional[str] = Field(None, pattern=r"^(male|female|other|)$")
    notify_meds: bool = False
    notify_periods: bool = False
    notify_water: bool = False


# ─── Water Schemas ───────────────────────────────────────────────────────────

class WaterLogRequest(BaseModel):
    glasses: int = Field(1, ge=1, le=50)


class WaterLogResponse(BaseModel):
    glasses: int
    ml: float


# ─── Calorie Schemas ─────────────────────────────────────────────────────────

class CalorieLogRequest(BaseModel):
    meal_type: str = Field("snack", pattern=r"^(breakfast|lunch|dinner|snack)$")
    description: str = Field("", max_length=500)
    calories: float = Field(0, ge=0, le=10000)
    protein_g: float = Field(0, ge=0, le=1000)
    carbs_g: float = Field(0, ge=0, le=1000)
    fat_g: float = Field(0, ge=0, le=1000)


class CalorieLogResponse(BaseModel):
    id: int
    calories: float


# ─── Exercise Schemas ────────────────────────────────────────────────────────

class ExerciseLogRequest(BaseModel):
    exercise_type: str = Field("", max_length=100)
    duration_min: float = Field(0, ge=0, le=1440)
    calories_burned: float = Field(0, ge=0, le=10000)
    notes: str = Field("", max_length=500)


class ExerciseLogResponse(BaseModel):
    id: int
    duration: float
    burned: float


# ─── Medication Schemas ──────────────────────────────────────────────────────

class MedicationCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    dosage: str = Field("", max_length=100)
    frequency: str = Field("daily", pattern=r"^(daily|twice-daily|weekly|as-needed)$")
    time_of_day: str = Field("morning", pattern=r"^(morning|afternoon|evening|bedtime)$")
    pills_remaining: int = Field(30, ge=0, le=10000)


class MedicationResponse(BaseModel):
    id: int
    name: str
    dosage: str
    frequency: str
    time: str
    pills_remaining: int
    needs_refill: bool


# ─── Sleep Schemas ───────────────────────────────────────────────────────────

class SleepLogRequest(BaseModel):
    hours: float = Field(0, ge=0, le=24)
    quality: int = Field(3, ge=1, le=5)


class SleepLogResponse(BaseModel):
    hours: float
    quality: int


# ─── Mood Schemas ────────────────────────────────────────────────────────────

class MoodLogRequest(BaseModel):
    mood: int = Field(3, ge=1, le=5)
    energy: int = Field(3, ge=1, le=5)
    stress: int = Field(3, ge=1, le=5)
    notes: str = Field("", max_length=500)


class MoodLogResponse(BaseModel):
    mood: int
    energy: int
    stress: int


# ─── Period Schemas ──────────────────────────────────────────────────────────

class PeriodLogRequest(BaseModel):
    flow_intensity: str = Field("medium", pattern=r"^(spotting|light|medium|heavy)$")
    symptoms: str = Field("", max_length=500)
    notes: str = Field("", max_length=500)


class PeriodPhaseResponse(BaseModel):
    phase: Optional[str]
    cycle_day: Optional[int]
    next_period_date: Optional[str] = None
    cycle_length: Optional[int] = None


# ─── Allergy Schemas ─────────────────────────────────────────────────────────

class AllergyCreateRequest(BaseModel):
    allergen: str = Field(..., min_length=1, max_length=200)
    severity: str = Field("moderate", pattern=r"^(mild|moderate|severe|life-threatening)$")
    reaction: str = Field("", max_length=500)
    emergency_contact: str = Field("", max_length=200)
    emergency_phone: str = Field("", max_length=50)


class AllergyResponse(BaseModel):
    id: int
    allergen: str
    severity: str
    reaction: str
    contact: str
    phone: str


# ─── Goal Schemas ────────────────────────────────────────────────────────────

class GoalUpdateRequest(BaseModel):
    water_glasses: Optional[int] = Field(None, ge=1, le=30)
    calories: Optional[int] = Field(None, ge=500, le=10000)
    exercise_min: Optional[int] = Field(None, ge=5, le=300)
    sleep_hours: Optional[float] = Field(None, ge=1, le=16)


class GoalResponse(BaseModel):
    water_glasses: int
    calories: int
    exercise_min: int
    sleep_hours: float


# ─── Weight Log Schemas ──────────────────────────────────────────────────────

class WeightLogRequest(BaseModel):
    weight_kg: float = Field(..., ge=5, le=500)
    notes: str = Field("", max_length=300)


class WeightLogResponse(BaseModel):
    id: int
    date: str
    weight_kg: float
    bmi: Optional[float]
    notes: str


# ─── Nutrition Search Schemas ────────────────────────────────────────────────

class NutritionSearchResponse(BaseModel):
    name: str
    serving: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


# ─── Stats / Streak Schemas ──────────────────────────────────────────────────

class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    total_active_days: int
    total_days_tracked: int


class MedAdherenceResponse(BaseModel):
    medication_id: int
    name: str
    total_expected: int
    total_taken: int
    adherence_pct: float
    last_taken: Optional[str]
